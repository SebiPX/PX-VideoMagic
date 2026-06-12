"""Render a video from an EDL.

Implements the HEURISTICS render pipeline in the correct order:

  1. Per-segment extract with color grade + 30ms audio fades baked in
  2. Lossless -c copy concat into base.mp4
  3. If overlays or subtitles: single filter graph that overlays animations
     (with PTS shift so frame 0 lands at the overlay window start)
     and applies `subtitles` filter LAST → final.mp4

Optionally builds a master SRT from the per-source transcripts + EDL
output-timeline offsets, applies the proven force_style (2-word
UPPERCASE chunks, Helvetica 18 Bold, MarginV=35).

Usage:
    python helpers/render.py <edl.json> -o final.mp4
    python helpers/render.py <edl.json> -o preview.mp4 --preview
    python helpers/render.py <edl.json> -o final.mp4 --build-subtitles
    python helpers/render.py <edl.json> -o final.mp4 --no-subtitles
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from grade import get_preset, auto_grade_for_clip  # same directory
except Exception:
    def get_preset(name: str) -> str:
        return ""

    def auto_grade_for_clip(video, start=0.0, duration=None, verbose=False):  # type: ignore
        return "none", {}


# -------- Subtitle style (bold-overlay, proven at 1920×1080 and 1080×1920) --
#
# MarginV is NOT taste — it is a platform safe-zone rule.
# TikTok / IG Reels / Shorts UI (caption, username, music, right-rail actions)


# -------- Subtitle style (bold-overlay, proven at 1920×1080 and 1080×1920) --
#
# MarginV is NOT taste — it is a platform safe-zone rule.
# TikTok / IG Reels / Shorts UI (caption, username, music, right-rail actions)
# covers roughly the bottom ~25–30% of a 1080×1920 frame. Captions placed near
# the bottom edge get clipped or obscured by the UI. libass auto-scales the
# render canvas relative to PlayResY=288, so MarginV=90 lands the caption
# baseline roughly 30% up from the bottom on any aspect — clear of the UI on
# every major vertical-video platform. Do not drop this below ~75 without a
# specific reason.
SUB_STYLES = {
    "classic_bold": (
        "FontName=Helvetica,FontSize=18,Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=90"
    ),
    "neon_pop": (
        "FontName=Anton,FontSize=22,Bold=0,"
        "PrimaryColour=&H0000FFFF,OutlineColour=&H00FF00FF,BackColour=&H00000000,"
        "BorderStyle=1,Outline=3,Shadow=0,"
        "Alignment=2,MarginV=90"
    ),
    "clean_minimalist": (
        "FontName=Inter,FontSize=16,Bold=0,"
        "PrimaryColour=&H00E0E0E0,OutlineColour=&H00333333,BackColour=&H00000000,"
        "BorderStyle=1,Outline=1,Shadow=1,"
        "Alignment=2,MarginV=90"
    ),
    "pixelschickeria": (
        "FontName=GT America,FontSize=20,Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00E83A14,BackColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=90"
    ),
    "translated_dmax": (
        "FontName=GT America,FontSize=20,Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,"
        "BorderStyle=1,Outline=0,Shadow=2,"
        "Alignment=2,MarginV=45"
    )
}


# -------- Helpers ------------------------------------------------------------


def run(cmd: list[str], quiet: bool = False) -> None:
    if not quiet:
        print(f"  $ {' '.join(str(c) for c in cmd[:6])}{' …' if len(cmd) > 6 else ''}")
    subprocess.run(cmd, check=True)


def resolve_grade_filter(grade_field: str | None) -> str:
    """The EDL's 'grade' field can be a preset name, a raw ffmpeg filter, or 'auto'.

    Returns the filter string to embed into the per-segment -vf chain.
    For 'auto', returns the sentinel "__AUTO__" which is resolved per-segment.
    """
    if not grade_field:
        return ""
    if grade_field == "auto":
        return "__AUTO__"
    # Preset names are short identifiers, filter strings contain '=' or ','.
    if re.fullmatch(r"[a-zA-Z0-9_\-]+", grade_field):
        try:
            return get_preset(grade_field)
        except KeyError:
            print(f"warning: unknown preset '{grade_field}', using as raw filter")
            return grade_field
    return grade_field


def resolve_path(maybe_path: str, base: Path) -> Path:
    """Resolve a path that may be absolute or relative to `base`."""
    p = Path(maybe_path)
    if p.is_absolute():
        return p
    return (base / p).resolve()


# -------- HDR -> SDR tone mapping (HLG / PQ sources) --------------------------
#
# iPhone defaults to HLG HDR in Rec.2020 (and many mirrorless cameras ship PQ).
# If the source is HDR and we only downconvert bit depth (yuv420p10le -> yuv420p)
# without tone-mapping, the output is 8-bit but still carries HLG/PQ transfer
# metadata. Players that honor the metadata (screen recorders, most social
# upload re-encodes) interpret 8-bit values in an HDR container and the result
# looks oversaturated / blown out. QuickTime on macOS can hide this locally —
# screen recording and uploaded renders cannot.
#
# Fix: detect HDR via color_transfer and prepend a zscale+tonemap chain to the
# vf graph so the output is clean Rec.709 SDR.

HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}  # PQ (HDR10) and HLG

TONEMAP_CHAIN = (
    "zscale=t=linear:npl=100,"
    "format=gbrpf32le,"
    "zscale=p=bt709,"
    "tonemap=tonemap=hable:desat=0,"
    "zscale=t=bt709:m=bt709:r=tv,"
    "format=yuv420p"
)


def is_hdr_source(video: Path) -> bool:
    """Return True if the source uses a PQ or HLG transfer function."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=color_transfer",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip() in HDR_TRANSFERS
    except subprocess.CalledProcessError:
        return False


def get_video_dimensions(video: Path) -> tuple[int, int]:
    """Return the width and height of the video."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=p=0", str(video)],
            capture_output=True, text=True, check=True,
        )
        w, h = map(int, out.stdout.strip().split(","))
        return w, h
    except Exception:
        return 1080, 1920

def is_portrait_source(video: Path) -> bool:
    """Return True if the video's height > width (portrait / vertical)."""
    w, h = get_video_dimensions(video)
    return h > w


def get_video_fps(video_path: Path) -> float:
    """Extract the true framerate of the source video."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0",
            str(video_path)
        ]
        out = subprocess.check_output(cmd, text=True).strip()
        if '/' in out:
            num, den = out.split('/')
            return float(num) / float(den)
        return float(out)
    except Exception:
        return 30.0


# -------- Per-segment extraction (Rule 2 + Rule 3) --------------------------


def extract_segment(
    source: Path,
    seg_start: float,
    duration: float,
    grade_filter: str,
    out_path: Path,
    preview: bool = False,
    draft: bool = False,
    fps: float = 30.0,
):
    """Extract one segment from the source video.
    
    Applies the video grade (if any) and 30ms audio fades at both edges
    to prevent audio pops when concatenating (Hard Rule 3).
    Output is re-encoded with fast preset so all segments share the same timeline/codec.
    """
    vf_parts = ["scale=1920:-2"]
    if grade_filter and grade_filter.lower() != "none":
        vf_parts.append(grade_filter)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    portrait = is_portrait_source(source)
    if draft:
        scale = "scale=-2:1280" if portrait else "scale=1280:-2"
    else:
        scale = "scale=-2:1920" if portrait else "scale=1920:-2"

    vf_parts: list[str] = []
    if is_hdr_source(source):
        vf_parts.append(TONEMAP_CHAIN)
    vf_parts.append(scale)
    if grade_filter and grade_filter.lower() != "none":
        vf_parts.append(grade_filter)
    vf = ",".join(vf_parts)

    # 30ms audio fades at both edges (Rule 3) — prevent pops
    fade_out_start = max(0.0, duration - 0.03)
    af = f"afade=t=in:st=0:d=0.03,afade=t=out:st={fade_out_start:.3f}:d=0.03"

    if draft:
        preset, crf = "ultrafast", "28"
    elif preview:
        preset, crf = "medium", "22"
    else:
        preset, crf = "fast", "20"

    cmd = ["ffmpeg", "-y"]
    
    is_image = str(source).lower().endswith(('.jpg', '.jpeg', '.png'))
    
    if is_image:
        cmd.extend([
            "-loop", "1",
            "-framerate", str(round(fps, 3)),
            "-t", f"{duration:.3f}",
            "-i", str(source),
            "-f", "lavfi",
            "-t", f"{duration:.3f}",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"
        ])
    else:
        cmd.extend([
            "-ss", f"{seg_start:.3f}",
            "-i", str(source),
            "-t", f"{duration:.3f}"
        ])
        
    cmd.extend([
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264", "-preset", preset, "-crf", crf,
        "-pix_fmt", "yuv420p", "-r", str(round(fps, 3)),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        str(out_path),
    ])
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def extract_all_segments(
    edl: dict,
    edit_dir: Path,
    preview: bool,
    draft: bool = False,
    fps: float = 30.0,
) -> list[Path]:
    """Extract every EDL range into edit_dir/clips_graded/seg_NN.mp4.
    Returns the ordered list of segment paths.

    If the EDL `grade` is "auto", analyze each segment range with
    `auto_grade_for_clip` and apply a per-segment subtle correction.
    Otherwise, apply the same preset/raw filter to every segment.
    """
    resolved = resolve_grade_filter(edl.get("grade"))
    is_auto = resolved == "__AUTO__"
    clips_dir = edit_dir / (
        "clips_draft" if draft else ("clips_preview" if preview else "clips_graded")
    )
    clips_dir.mkdir(parents=True, exist_ok=True)

    ranges = edl["ranges"]
    sources = edl["sources"]

    seg_paths: list[Path] = []
    print(f"extracting {len(ranges)} segment(s) -> {clips_dir.name}/")
    if is_auto:
        print("  (auto-grade per segment: analyzing each range)")
    for i, r in enumerate(ranges):
        src_name = r["source"]
        src_path = resolve_path(sources[src_name], edit_dir)
        start = float(r["start"])
        end = float(r["end"])
        duration = end - start
        out_path = clips_dir / f"seg_{i:02d}_{src_name}.mp4"

        if is_auto:
            seg_filter, _stats = auto_grade_for_clip(src_path, start=start, duration=duration, verbose=False)
        else:
            seg_filter = resolved

        note = r.get("beat") or r.get("note") or ""
        print(f"  [{i:02d}] {src_name}  {start:7.2f}-{end:7.2f}  ({duration:5.2f}s)  {note}")
        if is_auto:
            print(f"        grade: {seg_filter or '(none)'}")
        extract_segment(src_path, start, duration, seg_filter, out_path, preview=preview, draft=draft, fps=fps)
        seg_paths.append(out_path)

    return seg_paths


# -------- Lossless concat ----------------------------------------------------


def concat_segments(segment_paths: list[Path], out_path: Path, edit_dir: Path) -> None:
    """Lossless concat via the concat demuxer. No re-encode."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    concat_list = edit_dir / "_concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segment_paths), encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        "-movflags", "+faststart",
        str(out_path),
    ]
    print(f"concat -> {out_path.name}")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    concat_list.unlink(missing_ok=True)


# -------- Master SRT (Rule 5) ------------------------------------------------


PUNCT_BREAK = set(".,!?;:")


def _srt_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    h, rem = divmod(total_ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _words_in_range(transcript: dict, t_start: float, t_end: float) -> list[dict]:
    out: list[dict] = []
    for w in transcript.get("words", []):
        if w.get("type") != "word":
            continue
        ws = w.get("start")
        we = w.get("end")
        if ws is None or we is None:
            continue
        if we <= t_start or ws >= t_end:
            continue
        out.append(w)
    return out


def translate_srt_file(srt_path: Path, language: str) -> None:
    print(f"  translating subtitles to {language} via Gemini...")
    import os
    try:
        from google import genai
    except ImportError:
        print("  warning: google-genai not installed, cannot translate subtitles.")
        return
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("  warning: GEMINI_API_KEY not set, cannot translate subtitles.")
        return
        
    client = genai.Client(api_key=api_key)
    
    text = srt_path.read_text(encoding="utf-8")
    
    sys_prompt = f"Du bist ein professioneller Untertitel-Übersetzer. Übersetze die folgende SRT-Datei in die Sprache: {language}. Behalte die exakte Struktur, das SRT Format, alle Timestamps und Nummern sowie leere Zeilen bei. Antworte AUSSCHLIESSLICH mit dem validen übersetzten SRT-Code. Keine Einleitung, kein Markdown-Codeblock, NUR der reine SRT Text."
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[sys_prompt, text]
        )
        translated_text = response.text.strip()
        if translated_text.startswith("```"):
            lines = translated_text.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1].startswith("```"): lines = lines[:-1]
            translated_text = "\n".join(lines).strip()
            
        srt_path.write_text(translated_text, encoding="utf-8")
        print(f"  subtitles successfully translated to {language}.")
    except Exception as e:
        print(f"  error during subtitle translation: {e}")


def build_master_srt(edl: dict, edit_dir: Path, out_path: Path) -> None:
    """Build an output-timeline SRT from per-source transcripts.

    - 2-word chunks (break on any punctuation in between)
    - UPPERCASE text
    - Output times computed as word.start - segment_start + segment_offset
    """
    transcripts_dir = edit_dir / "transcripts"
    sources = edl["sources"]

    entries: list[tuple[float, float, str]] = []
    seg_offset = 0.0

    for r in edl["ranges"]:
        src_name = r["source"]
        seg_start = float(r["start"])
        seg_end = float(r["end"])
        seg_duration = seg_end - seg_start

        tr_path = transcripts_dir / f"{src_name}.json"
        if not tr_path.exists():
            print(f"  no transcript for {src_name}, skipping captions for this segment")
            seg_offset += seg_duration
            continue

        transcript = json.loads(tr_path.read_text())
        words_in_seg = _words_in_range(transcript, seg_start, seg_end)

        # Group into 2-word chunks, break on punctuation
        chunks: list[list[dict]] = []
        current: list[dict] = []
        for w in words_in_seg:
            text = (w.get("text") or "").strip()
            if not text:
                continue
            current.append(w)
            # Break if the current text ends in punctuation or we hit 2 words
            ends_in_punct = bool(text) and text[-1] in PUNCT_BREAK
            if len(current) >= 2 or ends_in_punct:
                chunks.append(current)
                current = []
        if current:
            chunks.append(current)

        for chunk in chunks:
            local_start = max(seg_start, chunk[0].get("start", seg_start))
            local_end = min(seg_end, chunk[-1].get("end", seg_end))
            out_start = max(0.0, local_start - seg_start) + seg_offset
            out_end = max(0.0, local_end - seg_start) + seg_offset
            if out_end <= out_start:
                out_end = out_start + 0.4
            text = " ".join((w.get("text") or "").strip() for w in chunk)
            text = re.sub(r"\s+", " ", text).strip()
            # Strip trailing punctuation for cleaner uppercase look
            text = text.rstrip(",;:")
            text = text.upper()
            entries.append((out_start, out_end, text))

        seg_offset += seg_duration

    # Sort and write as SRT
    entries.sort(key=lambda e: e[0])
    lines: list[str] = []
    for i, (a, b, t) in enumerate(entries, start=1):
        lines.append(str(i))
        lines.append(f"{_srt_timestamp(a)} --> {_srt_timestamp(b)}")
        lines.append(t)
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"master SRT -> {out_path.name} ({len(entries)} cues)")


def build_remotion_subtitles(
    edl: dict, edit_dir: Path, out_path: Path, highlight_color: str, highlight_shape: str, fps: float,
    font_family: str, font_weight: str, text_case: str, font_size: int = 20, y_position: int = 15, width: int = 1080, height: int = 1920, pill_radius: int = 20,
    pop_in_animation: bool = True, keep_punctuation: bool = False, shape_padding: int = 10
) -> None:
    """Build a transparent WebM subtitle overlay using Remotion."""
    transcripts_dir = edit_dir / "transcripts"
    
    entries: list[dict] = []
    seg_offset = 0.0

    for r in edl["ranges"]:
        src_name = r["source"]
        seg_start = float(r["start"])
        seg_end = float(r["end"])
        seg_duration = seg_end - seg_start

        tr_path = transcripts_dir / f"{src_name}.json"
        if not tr_path.exists():
            seg_offset += seg_duration
            continue

        transcript = json.loads(tr_path.read_text())
        words_in_seg = _words_in_range(transcript, seg_start, seg_end)
        
        for w in words_in_seg:
            local_start = max(seg_start, w.get("start", seg_start))
            local_end = min(seg_end, w.get("end", seg_end))
            out_start = max(0.0, local_start - seg_start) + seg_offset
            out_end = max(0.0, local_end - seg_start) + seg_offset
            
            if out_end > out_start:
                entry = {
                    "start": out_start,
                    "end": out_end,
                    "text": (w.get("text") or "").strip()
                }
                if "y_position_override" in r and r["y_position_override"] is not None:
                    entry["yPositionOverride"] = float(r["y_position_override"])
                entries.append(entry)

        seg_offset += seg_duration

    # Write props JSON for Remotion
    props_path = edit_dir / "remotion_props.json"
    
    # Calculate duration (exactly the length of the base video)
    duration_frames = max(10, int(round(seg_offset * fps)))
    props = {
        "words": entries,
        "highlightColor": highlight_color,
        "highlightShape": highlight_shape,
        "pillRadius": pill_radius,
        "popInAnimation": pop_in_animation,
        "keepPunctuation": keep_punctuation,
        "shapePadding": shape_padding,
        "durationInFrames": duration_frames,
        "fps": fps,
        "width": width,
        "height": height,
        "fontFamily": font_family,
        "fontWeight": font_weight,
        "textCase": text_case,
        "fontSize": font_size,
        "yPosition": y_position
    }
    props_path.write_text(json.dumps(props), encoding="utf-8")
    
    print(f"remotion subs -> generating {out_path.name} ({len(entries)} words)...")
    
    if getattr(sys, 'frozen', False):
        remotion_dir = Path(sys.executable).parent / "video-use" / "remotion-subs"
    else:
        remotion_dir = Path(__file__).parent.parent / "remotion-subs"
        
    if getattr(sys, 'frozen', False):
        packed_modules = remotion_dir / "node_modules_packed"
        node_modules = remotion_dir / "node_modules"
        if packed_modules.exists():
            if node_modules.exists():
                import shutil
                shutil.rmtree(node_modules, ignore_errors=True)
            try:
                packed_modules.rename(node_modules)
            except Exception as e:
                print(f"Warning: Could not rename node_modules_packed: {e}")
                
    if not remotion_dir.exists():
        sys.exit(f"Remotion project not found in {remotion_dir}")
        
    is_win = sys.platform == "win32"
    cmd = [
        "npx.cmd" if is_win else "npx", "remotion", "render", "src/index.ts", "Subtitles",
        str(out_path.resolve()),
        "--codec=prores",
        "--prores-profile=4444",
        "--image-format=png",
        "--pixel-format=yuva444p10le",
        f"--props={props_path.resolve()}"
    ]
    
    # Use npx.cmd on Windows without shell=True to preserve argument quotes
    is_win = sys.platform == "win32"
    if is_win:
        cmd[0] = "npx.cmd"
    subprocess.run(cmd, cwd=str(remotion_dir), check=True)
        
    props_path.unlink(missing_ok=True)



# -------- Loudness normalization (social-ready audio) -----------------------


# Social-media standard: -14 LUFS integrated, -1 dBTP peak, LRA 11 LU.
# Matches YouTube / Instagram / TikTok / X / LinkedIn normalization targets.
LOUDNORM_I = -14.0
LOUDNORM_TP = -1.0
LOUDNORM_LRA = 11.0


def measure_loudness(video_path: Path) -> dict[str, str] | None:
    """Run ffmpeg loudnorm first pass and parse the JSON measurement.

    Returns a dict with measured_i, measured_tp, measured_lra, measured_thresh,
    target_offset, or None if measurement failed.
    """
    filter_str = (
        f"loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}:LRA={LOUDNORM_LRA}:print_format=json"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-nostats",
        "-i", str(video_path),
        "-af", filter_str,
        "-vn", "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # loudnorm prints the JSON to stderr at the end of the run
    stderr = proc.stderr

    # Find the JSON block — loudnorm output contains a `{ ... }` block
    start = stderr.rfind("{")
    end = stderr.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(stderr[start : end + 1])
    except json.JSONDecodeError:
        return None
    needed = {"input_i", "input_tp", "input_lra", "input_thresh", "target_offset"}
    if not needed.issubset(data.keys()):
        return None
    return data


def apply_loudnorm_two_pass(
    input_path: Path,
    output_path: Path,
    preview: bool = False,
) -> bool:
    """Run two-pass loudnorm on input_path, write normalized copy to output_path.

    Returns True on success, False if measurement failed (caller should fall
    back to copying the input unchanged).

    In preview mode, skips the measurement pass and uses a one-pass approximation
    for speed. Final mode always does the proper two-pass.
    """
    if preview:
        # One-pass approximation — faster, slightly less accurate.
        filter_str = f"loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}:LRA={LOUDNORM_LRA}"
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-nostats",
            "-i", str(input_path),
            "-c:v", "copy",
            "-af", filter_str,
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart",
            str(output_path),
        ]
        print(f"  loudnorm (1-pass preview) -> {output_path.name}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return True

    # Full two-pass
    print(f"  loudnorm pass 1: measuring {input_path.name}")
    measurement = measure_loudness(input_path)
    if measurement is None:
        print("  loudnorm measurement failed — falling back to 1-pass")
        return apply_loudnorm_two_pass(input_path, output_path, preview=True)

    print(f"    measured: I={measurement['input_i']} LUFS  "
          f"TP={measurement['input_tp']}  LRA={measurement['input_lra']}")

    filter_str = (
        f"loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}:LRA={LOUDNORM_LRA}"
        f":measured_I={measurement['input_i']}"
        f":measured_TP={measurement['input_tp']}"
        f":measured_LRA={measurement['input_lra']}"
        f":measured_thresh={measurement['input_thresh']}"
        f":offset={measurement['target_offset']}"
        f":linear=true"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-nostats",
        "-i", str(input_path),
        "-c:v", "copy",
        "-af", filter_str,
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        str(output_path),
    ]
    print(f"  loudnorm pass 2: normalizing -> {output_path.name}")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return True


# -------- Final compositing (Rule 1 + Rule 4) -------------------------------





def build_final_composite(
    base_path: Path,
    overlays: list[dict],
    subtitles_path: Path | None,
    out_path: Path,
    edit_dir: Path,
    sub_style: str = "classic_bold",
    font_size: int = 20,
    y_position: int = 15,
) -> None:
    """Final pass: base -> overlays (PTS-shifted) -> logo -> subtitles LAST -> out."""
    
    logo_path = edit_dir / "logo.png"
    has_logo = logo_path.exists()
    has_overlays = bool(overlays)
    has_subs = subtitles_path is not None and subtitles_path.exists()

    if not has_overlays and not has_subs and not has_logo:
        # Nothing to do — just rename/copy base to final name
        run(["ffmpeg", "-y", "-i", str(base_path), "-c", "copy", str(out_path)], quiet=True)
        return

    input_files_count = 1
    inputs: list[str] = ["-i", str(base_path)]
    for ov in overlays:
        ov_path = resolve_path(ov["file"], edit_dir)
        inputs += ["-i", str(ov_path)]
        input_files_count += 1

    filter_parts: list[str] = []
    # PTS-shift every overlay so its frame 0 lands at start_in_output
    for idx, ov in enumerate(overlays, start=1):
        t = float(ov["start_in_output"])
        filter_parts.append(f"[{idx}:v]setpts=PTS-STARTPTS+{t}/TB[a{idx}]")

    # Chain overlays on top of base
    current = "[0:v]"
    for idx, ov in enumerate(overlays, start=1):
        t = float(ov["start_in_output"])
        dur = float(ov["duration"])
        end = t + dur
        next_label = f"[v{idx}]"
        filter_parts.append(
            f"{current}[a{idx}]overlay=enable='between(t,{t:.3f},{end:.3f})'{next_label}"
        )
        current = next_label

    # Logo BUG
    if has_logo:
        logo_idx = input_files_count
        input_files_count += 1
        inputs += ["-i", str(logo_path)]
        next_label = "[withlogo]"
        # Put logo top right with 30px padding
        filter_parts.append(f"[{logo_idx}:v]scale=200:-1[logo];{current}[logo]overlay=main_w-overlay_w-30:30{next_label}")
        current = next_label

    # Subtitles LAST — Rule 1
    if has_subs:
        if subtitles_path.suffix.lower() == ".mov":
            # Overlay transparent mov (Remotion output)
            ov_idx = input_files_count
            input_files_count += 1
            inputs += ["-i", str(subtitles_path)]

            # We don't PTS shift the subtitle track because Remotion renders the exact length
            bw, bh = get_video_dimensions(base_path)
            next_label = "[finalout]"
            filter_parts.append(
                f"[{ov_idx}:v]scale={bw}:{bh}[subs];{current}[subs]overlay=enable='between(t,0,99999)':shortest=1{next_label}"
            )
            current = next_label
        else:
            # Classic ASS/SRT subtitles
            srt_abs = str(subtitles_path.resolve()).replace("\\", "/")
            srt_abs = srt_abs.replace(":", "\\:")
            style_str = SUB_STYLES.get(sub_style, SUB_STYLES["classic_bold"])
            
            # Apply dynamic font_size and y_position to SRT style
            # Default Font Size is around 18-22 in styles. Scale font_size (10-60) from UI.
            # Default MarginV is 90 in styles. Scale y_position (5-50) from UI.
            # A rough mapping: font_size directly, y_position * 6 for MarginV.
            style_str = re.sub(r"FontSize=\d+", f"FontSize={font_size}", style_str)
            style_str = re.sub(r"MarginV=\d+", f"MarginV={y_position * 6}", style_str)

            filter_parts.append(f"{current}subtitles='{srt_abs}':force_style='{style_str}'[out]")
            current = "[out]"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", ";".join(filter_parts) if filter_parts else "",
        "-map", current if filter_parts else "0:v",
        "-map", "0:a?",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path)
    ]
    run(cmd)

def standardize_and_concat_assets(main_video: Path, edit_dir: Path, out_path: Path):
    opener = edit_dir / "opener.mp4"
    closer = edit_dir / "closer.mp4"
    
    if not opener.exists() and not closer.exists():
        run(["ffmpeg", "-y", "-i", str(main_video), "-c", "copy", str(out_path)], quiet=True)
        return
        
    print("  standardizing and concatenating opener/closer assets...")
    bw, bh = get_video_dimensions(main_video)
    fps = get_video_fps(main_video)
    
    def standardize(p: Path, name: str) -> Path:
        out = edit_dir / f"{name}_std.mp4"
        cmd = [
            "ffmpeg", "-y", "-i", str(p),
            "-vf", f"scale={bw}:{bh}:force_original_aspect_ratio=decrease,pad={bw}:{bh}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(fps),
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            str(out)
        ]
        run(cmd, quiet=True)
        return out

    parts = []
    if opener.exists():
        parts.append(standardize(opener, "opener"))
    
    # We must also standardize the main video audio to 48000hz 192k just to be perfectly sure they concat cleanly
    main_std = edit_dir / "main_std.mp4"
    run([
        "ffmpeg", "-y", "-i", str(main_video),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(main_std)
    ], quiet=True)
    parts.append(main_std)
    
    if closer.exists():
        parts.append(standardize(closer, "closer"))
        
    concat_list = edit_dir / "_concat_assets.txt"
    concat_list.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(out_path)
    ], quiet=True)
    
    concat_list.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render an EDL JSON into a final video")
    ap.add_argument("edl", type=Path, help="Path to EDL JSON file")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Output MP4 path")
    ap.add_argument("--preview", action="store_true", help="Render 720p with faster encoding")
    ap.add_argument("--draft", action="store_true", help="Ultra-fast 480p draft render")
    ap.add_argument("--no-subtitles", action="store_true", help="Skip subtitles completely")
    ap.add_argument("--build-subtitles", action="store_true", help="Rebuild master.srt/webm from EDL even if one exists")
    ap.add_argument("--no-loudnorm", action="store_true", help="Skip final -14 LUFS loudness normalization pass")
    ap.add_argument("--sub-style", type=str, default="classic_bold", help="Subtitle style to apply")
    ap.add_argument("--highlight-color", type=str, default="#00FFFF", help="Remotion highlight color")
    ap.add_argument("--highlight-shape", type=str, default="skew", help="Remotion highlight shape")
    ap.add_argument("--pill-radius", type=int, default=20, help="Pill box corner radius")
    ap.add_argument("--shape-padding", type=int, default=10, help="Padding/margin around the word for shapes")
    ap.add_argument("--disable-pop-in", action="store_true", help="Disable the pop-in animation on words")
    ap.add_argument("--keep-punctuation", action="store_true", help="Keep punctuation marks in subtitles")
    ap.add_argument("--font-family", type=str, default="'GT America', Helvetica, Arial, sans-serif")
    ap.add_argument("--font-weight", type=str, default="bold")
    ap.add_argument("--text-case", type=str, default="uppercase")
    ap.add_argument("--subtitle-language", type=str, default="Original", help="Language to translate subtitles to")
    ap.add_argument("--font-size", type=int, default=20)
    ap.add_argument("--y-position", type=int, default=15)
    args = ap.parse_args()

    edl_path = args.edl.resolve()
    if not edl_path.exists():
        sys.exit(f"EDL not found: {edl_path}")

    edl = json.loads(edl_path.read_text())
    edit_dir = edl_path.parent
    out_path = args.output.resolve()

    # Add ~6 frames (0.2s) padding to the end of every cut to prevent abrupt audio cutoffs
    for r in edl.get("ranges", []):
        r["end"] = float(r["end"]) + 0.2

    fps = 30.0
    width, height = 1080, 1920
    if edl.get("sources"):
        first_src_path = resolve_path(list(edl["sources"].values())[0], edit_dir)
        fps = get_video_fps(first_src_path)
        width, height = get_video_dimensions(first_src_path)
        # Handle draft/preview dimension scaling
        if args.draft:
            if height > width:
                width, height = 720, 1280
            else:
                width, height = 1280, 720
        elif args.preview:
            # Usually preview might be scaled, but we keep original dimensions for Remotion overlays to match the base video
            # Wait, extract_segment scales portrait draft to 1280 height, and landscape draft to 1280 width.
            # Normal output is 1920 long edge.
            if height > width:
                width, height = 1080, 1920
            else:
                width, height = 1920, 1080

    # 1. Extract per-segment (auto-grade per range if EDL grade is "auto")
    segment_paths = extract_all_segments(
        edl, edit_dir, preview=args.preview, draft=args.draft, fps=fps
    )

    # 2. Concat → base
    if args.draft:
        base_name = "base_draft.mp4"
    elif args.preview:
        base_name = "base_preview.mp4"
    else:
        base_name = "base.mp4"
    base_path = edit_dir / base_name
    concat_segments(segment_paths, base_path, edit_dir)

    # 3. Subtitles: build if requested, resolve final path
    subs_path: Path | None = None
    if not args.no_subtitles:
        if args.build_subtitles:
            # Karaoke-style Remotion breaks on translation (word sync). Fallback to SRT.
            if args.subtitle_language and args.subtitle_language.lower() != "original" and args.sub_style == "tiktok_dynamic":
                print("  translation requested: falling back to SRT subtitle style (translated_dmax)")
                args.sub_style = "translated_dmax"

            if args.sub_style == "tiktok_dynamic":
                subs_path = edit_dir / "subs.mov"
                build_remotion_subtitles(
                    edl, edit_dir, subs_path, args.highlight_color, args.highlight_shape, fps,
                    args.font_family, args.font_weight, args.text_case, args.font_size, args.y_position, width, height, args.pill_radius,
                    not args.disable_pop_in, args.keep_punctuation, args.shape_padding
                )
            else:
                subs_path = edit_dir / "master.srt"
                build_master_srt(edl, edit_dir, subs_path)
                if args.subtitle_language and args.subtitle_language.lower() != "original":
                    translate_srt_file(subs_path, args.subtitle_language)
        elif edl.get("subtitles"):
            subs_path = resolve_path(edl["subtitles"], edit_dir)
            if not subs_path.exists():
                print(f"warning: subtitles path in EDL does not exist: {subs_path}")
                subs_path = None

    # 4. Composite (overlays + subtitles LAST) -> intermediate (pre-loudnorm) path
    overlays = edl.get("overlays") or []
    tmp_composite = edit_dir / "composite.mp4"
    build_final_composite(base_path, overlays, subs_path, tmp_composite, edit_dir, args.sub_style, args.font_size, args.y_position)
    
    # 5. Loudnorm
    if args.no_loudnorm:
        tmp_loud = tmp_composite
    else:
        tmp_loud = out_path.with_suffix(".prenorm.mp4")
        print(f"loudness normalization -> social-ready (-14 LUFS / -1 dBTP / LRA 11)")
        apply_loudnorm_two_pass(tmp_composite, tmp_loud, preview=args.draft)
        
    # 6. Concat Assets (Opener/Closer)
    standardize_and_concat_assets(tmp_loud, edit_dir, out_path)
    
    if not args.no_loudnorm:
        tmp_loud.unlink(missing_ok=True)
    if tmp_composite != tmp_loud:
        tmp_composite.unlink(missing_ok=True)

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"\ndone: {out_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
