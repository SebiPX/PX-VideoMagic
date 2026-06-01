import os
import sys
import json
import uuid
import subprocess
import glob
from pathlib import Path
from google import genai
from elevenlabs_tts import generate_speech
import transcribe

def get_audio_duration(file_path):
    # Use ffprobe to get exact duration
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", str(file_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0

def generate_script(prompt: str, scene_count: int = 5, scene_hints: list = []):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    client = genai.Client(api_key=api_key, http_options={'timeout': 300000})
    
    system_instruction = f"""
    You are an expert video script writer and motion graphics director. Generate a script for a short video based on the user's prompt.
    CRITICAL: The video MUST have EXACTLY {scene_count} scenes. Do not return more or fewer scenes under any circumstances. You must return exactly {scene_count} JSON objects in the array.
    The script must be returned as a JSON array of scenes. 
    Each scene must have:
    - "speech": The exact spoken text for the voice over.
    - "visual_prompt": A highly detailed prompt for an AI image generator (Imagen 4) describing the background visual that matches the speech. Use photographic terms, cinematic lighting, and concrete imagery.
    - "graphics_prompt": A natural language description of the Typo-Animations or animated graphics that should appear on screen to support the speech (e.g. "Show the word 'MYSTERY' in huge bold orange letters sliding in from the left").
    """
    
    if scene_hints:
        system_instruction += "\nHere are user hints for the specific scenes. Try to incorporate them if possible:\n"
        for i, hint in enumerate(scene_hints):
            system_instruction += f"Scene {i+1}: {hint}\n"
            
    system_instruction += """
    Example output format:
    [
      {
        "speech": "Black holes are the most mysterious objects in the universe.",
        "visual_prompt": "A cinematic, ultra-realistic rendering of a supermassive black hole with a glowing accretion disk in deep space, stunning colors, 8k resolution",
        "graphics_prompt": "The word 'MYSTERY' appears in large, bold orange typography, fading in slowly at the center of the screen, followed by the word 'UNIVERSE'."
      }
    ]
    Return ONLY valid JSON. Do not use markdown blocks.
    """
    
    client = genai.Client(api_key=api_key, http_options={'timeout': 300000})
    
    for attempt in range(3):
        try:
            result = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=dict(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    safety_settings=[
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
                    ]
                )
            )
            text = result.text.strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                print(f"Failed to parse Script JSON: {e}")
                return []
        except Exception as e:
            print(f"Gemini API attempt {attempt+1} failed: {e}")
            import time
            time.sleep(2)
    raise Exception("Gemini API script generation failed after 3 attempts.")

def generate_scene_visual(prompt: str, output_path: str, aspect_ratio: str = "9:16"):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options={'timeout': 300000})
    
    for attempt in range(3):
        try:
            result = client.models.generate_images(
                model='imagen-4.0-fast-generate-001',
                prompt=prompt,
                config=dict(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    output_mime_type="image/jpeg",
                    person_generation="allow_adult"
                )
            )
            if not result.generated_images:
                raise Exception("Imagen returned no images.")
            
            with open(output_path, "wb") as f:
                f.write(result.generated_images[0].image.image_bytes)
            return
        except Exception as e:
            print(f"Imagen API attempt {attempt+1} failed: {e}")
            import time
            time.sleep(2)
            
    print(f"Fallback: generating default image for {output_path}")
    generate_blank_image(output_path, aspect_ratio)

def generate_blank_image(output_path: str, aspect_ratio: str = "9:16"):
    w, h = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}", "-frames:v", "1", output_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def generate_hyperframe_code(graphics_prompt: str, words_timing: list, duration: float, motion_graphics_only: bool = False, visual_style: str = "dynamic"):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'timeout': 300000})
    
    timing_str = "\n".join([f"Word: '{w['text']}' -> Start: {w['start']:.2f}s, End: {w['end']:.2f}s" for w in words_timing])
    
    if motion_graphics_only:
        bg_instruction = "CRITICAL: You are generating the FULL SCREEN video. DO NOT make the background transparent! Create a rich, immersive animated background (e.g., dynamic gradients, moving shapes, solid colors) using CSS/HTML. CRITICAL: The parent container is already 1080x1920. DO NOT use vw or vh units for sizing! Use width: 100%; height: 100%; for your main container."
    else:
        bg_instruction = "You are generating a transparent overlay. Use absolute positioning with 100% width/height."

    style_instructions = ""
    if visual_style == "tech":
        style_instructions = "STYLE: Tech & Futurism (Cyberpunk/HUD). Use neon colors (cyan, magenta, electric blue), glowing text-shadows, monospace fonts (e.g. 'Orbitron', 'Space Mono' from Google Fonts), grid backgrounds, and fast glitch or digital scanning effects."
    elif visual_style == "music":
        style_instructions = "STYLE: Music & Entertainment. Use vibrant, high-contrast colors, huge bold sans-serif fonts (e.g. 'Impact', 'Montserrat', 'Oswald' from Google Fonts), energetic bounce/pop-in animations, dynamic angled layouts (skewed divs), and fast-paced kinetic typography."
    elif visual_style == "art":
        style_instructions = "STYLE: Art & Design (Minimalist/Editorial). Use elegant serif fonts (e.g. 'Playfair Display', 'Cormorant' from Google Fonts) mixed with clean sans-serif. Use muted or pastel color palettes, lots of whitespace/negative space, slow smooth fades, and parallax-like gentle drifts."
    elif visual_style == "clean":
        style_instructions = "STYLE: Clean & Modern (HTML5 UP Style). Use flat design, highly structured blocks, semi-transparent overlays (glassmorphism), clean sans-serif (e.g. 'Inter', 'Roboto' from Google Fonts), and smooth slide-in animations."
    else:
        style_instructions = "STYLE: Dynamic Mixed Media. Use a balanced mix of shapes, frames, and modern typography with energetic but smooth animations."


    prompt = f"""
    You are a Motion Graphics Developer. You will generate HTML and GSAP code for a dynamic video.
    
    Graphics Request: {graphics_prompt}
    Total Scene Duration: {duration:.2f} seconds
    
    Exact Word Timings for synchronization:
    {timing_str}
    
    Your task is to generate:
    - "html_overlay": HTML/CSS for the visuals. Do not include <html> or <body> tags. {bg_instruction} 
      {style_instructions}
      CRITICAL LAYOUT INSTRUCTION: Do NOT just animate a single word in the center. Build complex, structured, poster-like layouts (Kinetic Typography). Group words into sentences or phrases and animate them staggered. Show multiple keywords flying in at different times and positions.
      Give elements clear class names or IDs. CRITICAL: DO NOT hide elements. DO NOT use opacity:0 or display:none in your inline styles or CSS. Elements must be fully visible by default so GSAP can animate them.
    - "animations": A JSON array of animation objects. Each object must have:
        - "selector": The CSS selector to animate (e.g., ".title", "#logo")
        - "effect": One of ["fade_in", "fade_in_up", "fade_in_down", "zoom_in", "slide_in_left", "slide_in_right", "pop_in"]
        - "start": The exact start time in seconds (float)
        - "duration": The duration in seconds (float)
    
    Output ONLY a JSON object with these two keys ("html_overlay" and "animations"). No markdown.
    """
    
    for attempt in range(3):
        try:
            result = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=dict(
                    response_mime_type="application/json",
                )
            )
            
            text = result.text.strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                print(f"Failed to parse GSAP JSON: {e}")
                return {"html_overlay": "", "gsap_code": ""}
        except Exception as e:
            print(f"Gemini GSAP attempt {attempt+1} failed: {e}")
            import time
            time.sleep(2)
            
    return {"html_overlay": "", "animations": []}

def review_and_fix_hyperframe_code(code_res: dict, duration: float) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'timeout': 300000})
    
    prompt = f"""
    You are an expert Code Reviewer. Review the following HTML/CSS and GSAP animations for a video overlay.
    
    The video duration is exactly {duration:.2f} seconds.
    
    CRITICAL RULES:
    1. No `opacity: 0` or `display: none` in CSS classes unless GSAP explicitly animates them to visibility (e.g. `opacity: 1`).
    2. No `vw` or `vh` units. The container is 1080x1920 or 1920x1080. Use `%`, `px`, `em`, `rem`.
    3. Ensure all CSS selectors in "animations" match elements in "html_overlay".
    4. Ensure all animations finish before the {duration:.2f} seconds mark.
    
    Input JSON:
    {json.dumps(code_res, indent=2)}
    
    Output ONLY a JSON object with the exact same structure ("html_overlay" and "animations"). Fix any violations. If no violations exist, return the input exactly. No markdown.
    """
    
    for attempt in range(2):
        try:
            result = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=dict(
                    response_mime_type="application/json",
                )
            )
            text = result.text.strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                print(f"Failed to parse Reviewer JSON: {e}")
                return code_res
        except Exception as e:
            print(f"Gemini Reviewer attempt {attempt+1} failed: {e}")
            import time
            time.sleep(2)
            
    return code_res

def build_safe_gsap_code(animations: list) -> str:
    code = ""
    for anim in animations:
        sel = anim.get("selector", "")
        eff = anim.get("effect", "fade_in")
        start = float(anim.get("start", 0))
        dur = float(anim.get("duration", 0.5))
        
        if not sel: continue
        
        if eff == "fade_in":
            code += f"tl.fromTo('{sel}', {{opacity: 0}}, {{opacity: 1, duration: {dur}}}, {start});\n"
        elif eff == "fade_in_up":
            code += f"tl.fromTo('{sel}', {{opacity: 0, y: 50}}, {{opacity: 1, y: 0, duration: {dur}}}, {start});\n"
        elif eff == "fade_in_down":
            code += f"tl.fromTo('{sel}', {{opacity: 0, y: -50}}, {{opacity: 1, y: 0, duration: {dur}}}, {start});\n"
        elif eff == "zoom_in":
            code += f"tl.fromTo('{sel}', {{opacity: 0, scale: 0.5}}, {{opacity: 1, scale: 1, duration: {dur}}}, {start});\n"
        elif eff == "slide_in_left":
            code += f"tl.fromTo('{sel}', {{opacity: 0, x: -100}}, {{opacity: 1, x: 0, duration: {dur}}}, {start});\n"
        elif eff == "slide_in_right":
            code += f"tl.fromTo('{sel}', {{opacity: 0, x: 100}}, {{opacity: 1, x: 0, duration: {dur}}}, {start});\n"
        elif eff == "pop_in":
            code += f"tl.fromTo('{sel}', {{opacity: 0, scale: 0}}, {{opacity: 1, scale: 1, ease: 'back.out(1.7)', duration: {dur}}}, {start});\n"
        else:
            code += f"tl.fromTo('{sel}', {{opacity: 0}}, {{opacity: 1, duration: {dur}}}, {start});\n"
            
    return code

def build_hyperframe_overlay(scene: dict, output_path: str, duration: float, aspect_ratio: str, project_dir: Path, scene_id: str):
    if aspect_ratio == "16:9":
        w, h = 1920, 1080
    else:
        w, h = 1080, 1920
        
    html_content = scene.get("html_overlay", "")
    gsap_code = scene.get("gsap_code", "")
    
    if not html_content and not gsap_code:
        return False
        
    hf_dir = project_dir / "animations" / scene_id
    hf_dir.mkdir(parents=True, exist_ok=True)
    
    index_html = f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
</head>
<body style="margin: 0; padding: 0; background: transparent; width: {w}px; height: {h}px; overflow: hidden;">
  <div data-composition-id="magic_{scene_id}" data-width="{w}" data-height="{h}" style="width: 100%; height: 100%; position: relative;">
     {html_content}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline();
    {gsap_code}
    tl.set({{}}, {{}}, {duration});
    window.__timelines['magic_{scene_id}'] = tl;
  </script>
</body>
</html>"""
    
    (hf_dir / "index.html").write_text(index_html, encoding="utf-8")
    
    cmd = [
        "npx.cmd" if sys.platform == "win32" else "npx",
        "--yes", "hyperframes", "render", ".",
        "--format", "webm",
        "-o", "overlay.webm"
    ]
    
    try:
        subprocess.run(cmd, cwd=str(hf_dir), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60)
        import shutil
        shutil.copy(str(hf_dir / "overlay.webm"), output_path)
        return True
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='replace').encode('cp1252', errors='replace').decode('cp1252')
        print(f"Hyperframes render failed for {scene_id}: {err_msg}")
        return False
    except subprocess.TimeoutExpired:
        print(f"Hyperframes render timed out for {scene_id} after 60s.")
        return False

def mux_scene(image_path: str, audio_path: str, output_path: str, duration: float, aspect_ratio: str = "9:16", overlay_path: str = None, motion_graphics_only: bool = False):
    if aspect_ratio == "16:9":
        w, h = 1920, 1080
    else:
        w, h = 1080, 1920
        
    frames = int(duration * 30) + 30
    # Remove jittery zoompan. Use static image scaling with pad to maintain aspect ratio perfectly.
    vf = f"[0:v]format=yuv420p,scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1:1,fps=30[bg]"
    
    if motion_graphics_only and overlay_path and os.path.exists(overlay_path):
        # Mux WebM directly with audio (ignoring image)
        cmd = [
            "ffmpeg", "-y",
            "-i", overlay_path,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a"
        ]
        vf = f"scale={w}:{h},setsar=1:1,fps=30" # Ensure target format
        map_v = "[v]" # Not used here, since we mapped directly
        cmd.extend([
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ])
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "30",
            "-t", str(duration),
            "-i", image_path,
            "-i", audio_path
        ]
        
        if overlay_path and os.path.exists(overlay_path):
            cmd.extend(["-c:v", "libvpx-vp9", "-i", overlay_path])
            vf += f";[bg][2:v]overlay=x=0:y=0:format=auto[v]"
            map_v = "[v]"
        else:
            map_v = "[bg]"
            
        cmd.extend([
            "-filter_complex", vf,
            "-map", map_v,
            "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ])

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=300)
    except subprocess.TimeoutExpired:
        print(f"FFmpeg muxing timed out for {output_path} after 300s.")
        # If it times out, the script will crash, which is better than hanging indefinitely.
        raise Exception(f"FFmpeg render timed out for {output_path}")

def build_magic_project(
    project_dir: Path, 
    script_scenes: list, 
    voice_id: str, 
    aspect_ratio: str = "9:16", 
    disable_hyperframes: bool = False,
    motion_graphics_only: bool = False,
    visual_style: str = "dynamic",
    progress_callback=None
):
    sources = {}
    ranges = []
    total_scenes = len(script_scenes)
    
    for i, scene in enumerate(script_scenes):
        scene_id = f"scene_{i:02d}"
        image_path = project_dir / f"{scene_id}.jpg"
        audio_path = project_dir / f"{scene_id}.mp3"
        video_path = project_dir / f"{scene_id}.mp4"
        
        # calculate base percent for this scene (start at 15%, end at 90%)
        base_percent = 15 + int((i / total_scenes) * 75)
        
        if progress_callback:
            progress_callback(f"Szene {i+1}/{total_scenes}: Audio generieren...", base_percent)
            
        print(f"Generating VO for scene {i}...")
        generate_speech(scene["speech"], voice_id, str(audio_path))
        dur = get_audio_duration(str(audio_path))
        dur += 1.5  # Add 1.5s padding so audio/animation doesn't cut off abruptly
        
        # Transcribe the audio to get exact word timings
        print(f"Transcribing scene {i}...")
        api_key_el = os.getenv("ELEVENLABS_API_KEY") or transcribe.load_api_key()
        transcript_path = transcribe.transcribe_one(audio_path, project_dir, api_key_el, verbose=False)
        with open(transcript_path, "r", encoding="utf-8") as f:
            t_data = json.load(f)
        words_timing = t_data.get("words", [])
        
        if motion_graphics_only:
            print(f"Skipping Imagen generation for scene {i} (Motion Graphics Only)")
            # Generate a blank image just as a fallback placeholder (so the file exists)
            generate_blank_image(str(image_path), aspect_ratio)
        else:
            if progress_callback:
                progress_callback(f"Szene {i+1}/{total_scenes}: Visuelles generieren...", base_percent + 4)
            print(f"Generating visual for scene {i}...")
            generate_scene_visual(scene["visual_prompt"], str(image_path), aspect_ratio)
        
        has_overlay = False
        overlay_webm = str(project_dir / f"{scene_id}_overlay.webm")
        if not disable_hyperframes:
            if progress_callback:
                progress_callback(f"Szene {i+1}/{total_scenes}: GSAP Code generieren...", base_percent + 8)
            print(f"Generating GSAP Code for scene {i}...")
            sys.stdout.flush()
            # Call Gemini with words to get precise HTML/GSAP code
            if "graphics_prompt" in scene:
                code_res = generate_hyperframe_code(scene["graphics_prompt"], words_timing, dur, motion_graphics_only=motion_graphics_only, visual_style=visual_style)
                
                if progress_callback:
                    progress_callback(f"Szene {i+1}/{total_scenes}: KI Review...", base_percent + 10)
                print(f"Reviewing and fixing GSAP Code for scene {i}...")
                sys.stdout.flush()
                code_res = review_and_fix_hyperframe_code(code_res, dur)
                
                scene["html_overlay"] = code_res.get("html_overlay", "")
                animations = code_res.get("animations", [])
                scene["gsap_code"] = build_safe_gsap_code(animations)
                
                if progress_callback:
                    progress_callback(f"Szene {i+1}/{total_scenes}: Animation rendern...", base_percent + 12)
                print(f"Generating Hyperframes overlay for scene {i}...")
                sys.stdout.flush()
                has_overlay = build_hyperframe_overlay(scene, overlay_webm, dur, aspect_ratio, project_dir, scene_id)
            else:
                print(f"Skipping GSAP for scene {i} (no graphics_prompt)")
        
        if progress_callback:
            progress_callback(f"Szene {i+1}/{total_scenes}: Szene zusammenfügen...", base_percent + 15)
        print(f"Muxing scene {i}...")
        mux_scene(str(image_path), str(audio_path), str(video_path), dur, aspect_ratio, overlay_webm if has_overlay else None, motion_graphics_only=motion_graphics_only)
        
        sources[scene_id] = f"{scene_id}.mp4"
        range_dict = {
            "source": scene_id,
            "start": 0.0,
            "end": dur,
            "beat": f"Scene {i}",
            "quote": scene["speech"]
        }
        if "y_position_override" in scene and scene["y_position_override"] is not None:
            range_dict["y_position_override"] = scene["y_position_override"]
            
        ranges.append(range_dict)
        
    edl = {
        "version": 1,
        "sources": sources,
        "ranges": ranges,
        "grade": "none",
        "overlays": []
    }
    
    with open(project_dir / "web_edl.json", "w", encoding="utf-8") as f:
        json.dump(edl, f, indent=2)
        
    return edl
