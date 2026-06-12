import os
import sys
import subprocess
import json
import re
import asyncio
import uuid
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from dotenv import load_dotenv
import sys
from google import genai

# Lade .env für API Keys
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(base_dir, ".env"))

app = FastAPI(title="VideoMagic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

projects_dir = os.path.join(base_dir, "projects")
os.makedirs(projects_dir, exist_ok=True)

from pathlib import Path
from pydantic import BaseModel

def get_settings_path():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        p = Path(appdata) / "PX-VideoMagic"
    else:
        p = Path.home() / ".px_videomagic"
    p.mkdir(parents=True, exist_ok=True)
    return p / "settings.json"

def load_settings():
    path = get_settings_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_settings(data):
    path = get_settings_path()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

settings = load_settings()
if settings.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = settings["GEMINI_API_KEY"]
if settings.get("ELEVENLABS_API_KEY"):
    os.environ["ELEVENLABS_API_KEY"] = settings["ELEVENLABS_API_KEY"]

class SettingsModel(BaseModel):
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""

@app.get("/api/settings")
def get_api_settings():
    s = load_settings()
    return {
        "gemini_api_key": s.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")),
        "elevenlabs_api_key": s.get("ELEVENLABS_API_KEY", os.environ.get("ELEVENLABS_API_KEY", ""))
    }

@app.post("/api/settings")
def update_api_settings(req: SettingsModel):
    s = load_settings()
    s["GEMINI_API_KEY"] = req.gemini_api_key
    s["ELEVENLABS_API_KEY"] = req.elevenlabs_api_key
    save_settings(s)
    
    os.environ["GEMINI_API_KEY"] = req.gemini_api_key
    os.environ["ELEVENLABS_API_KEY"] = req.elevenlabs_api_key
    return {"status": "success"}

app.mount("/projects_files", StaticFiles(directory=projects_dir), name="projects_files")

# Global progress state
progress_state = {
    "status": "idle",
    "step": "",
    "percent": 0
}

def set_progress(step: str, percent: int, status: str = "running"):
    progress_state["step"] = step
    progress_state["percent"] = percent
    progress_state["status"] = status

@app.get("/api/progress")
async def progress_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time progress updates"""
    async def event_generator():
        last_percent = -1
        last_step = ""
        while True:
            if await request.is_disconnected():
                break
            
            if progress_state["percent"] != last_percent or progress_state["step"] != last_step:
                last_percent = progress_state["percent"]
                last_step = progress_state["step"]
                yield f"data: {json.dumps({'step': last_step, 'percent': last_percent, 'status': progress_state['status']})}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/projects")
async def list_projects():
    projects = []
    for pid in os.listdir(projects_dir):
        pdir = os.path.join(projects_dir, pid)
        if os.path.isdir(pdir):
            pfile = os.path.join(pdir, "project.json")
            if os.path.exists(pfile):
                try:
                    with open(pfile, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta["id"] = pid
                        projects.append(meta)
                except Exception:
                    pass
    # Sort by created_at descending
    projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"status": "success", "projects": projects}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    pdir = os.path.join(projects_dir, project_id)
    pfile = os.path.join(pdir, "project.json")
    if not os.path.exists(pfile):
        raise HTTPException(status_code=404, detail="Project not found")
        
    with open(pfile, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    if meta.get("type") == "magic":
        transcript = None
        script_path = os.path.join(pdir, "magic_script.json")
        if os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    transcript = json.load(f)
            except Exception:
                pass
    else:
        # Read transcript
        transcript = None
        transcript_path = os.path.join(pdir, "transcripts", f"{meta.get('filename_no_ext')}.json")
        if os.path.exists(transcript_path):
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcript = json.load(f)
            except Exception:
                pass

    return {
        "status": "success",
        "project": meta,
        "transcript": transcript
    }


@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, request: Request):
    pdir = os.path.join(projects_dir, project_id)
    pfile = os.path.join(pdir, "project.json")
    if not os.path.exists(pfile):
        raise HTTPException(status_code=404, detail="Project not found")
        
    body = await request.json()
    with open(pfile, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    if "name" in body:
        meta["name"] = body["name"]
        
    with open(pfile, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    return {"status": "success", "project": meta}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    pdir = os.path.join(projects_dir, project_id)
    if os.path.exists(pdir):
        shutil.rmtree(pdir)
    return {"status": "success"}


@app.post("/api/transcribe")
async def process_transcribe(
    file: UploadFile = File(...),
    opener: UploadFile = File(None),
    closer: UploadFile = File(None),
    logo: UploadFile = File(None)
):
    """Step 1: Upload and Transcribe"""
    try:
        set_progress("Upload läuft...", 10)
        
        project_id = str(uuid.uuid4())
        pdir = os.path.join(projects_dir, project_id)
        os.makedirs(pdir, exist_ok=True)
        
        base_name, file_ext = os.path.splitext(file.filename)
        safe_filename = re.sub(r'[^\w\s-]', '', base_name).strip().replace(" ", "_").replace("-", "_") + file_ext
        file_path = os.path.join(pdir, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        if opener:
            with open(os.path.join(pdir, "opener.mp4"), "wb") as f:
                f.write(await opener.read())
        if closer:
            with open(os.path.join(pdir, "closer.mp4"), "wb") as f:
                f.write(await closer.read())
        if logo:
            with open(os.path.join(pdir, "logo.png"), "wb") as f:
                f.write(await logo.read())
            
        print(f"-> Datei hochgeladen: {file_path}")
        
        # Save project metadata
        meta = {
            "name": base_name,
            "filename": safe_filename,
            "filename_no_ext": os.path.splitext(safe_filename)[0],
            "created_at": datetime.now().isoformat(),
            "status": "transcribing"
        }
        with open(os.path.join(pdir, "project.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
                
        set_progress("Audio transkribieren...", 40)
        
        main_script = os.path.abspath(__file__)
        base_cmd = [sys.executable, "run_helper"] if getattr(sys, 'frozen', False) else [sys.executable, main_script, "run_helper"]
        
        # Transcribe. We pass the project dir as edit-dir. 
        # The transcribe helper generates transcript in <edit-dir>/transcripts/...
        subprocess.run(base_cmd + ["transcribe", file_path, "--edit-dir", pdir], cwd=base_dir, check=True)
        
        set_progress("Transkript zusammenstellen...", 90)
        
        filename_no_ext = meta["filename_no_ext"]
        transcript_path = os.path.join(pdir, "transcripts", f"{filename_no_ext}.json")
        
        if not os.path.exists(transcript_path):
            raise Exception("Transkription fehlgeschlagen: Keine JSON-Datei generiert.")
            
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
            
        # Update metadata
        meta["status"] = "edited"
        with open(os.path.join(pdir, "project.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        set_progress("Transkription abgeschlossen", 100, "success")
        
        return {
            "status": "success",
            "message": "Transkription erfolgreich!",
            "transcript": transcript_data,
            "project_id": project_id,
            "project": meta
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        set_progress("Fehler bei Transkription", 0, "error")
        return {"status": "error", "message": str(e)}

@app.post("/api/transcribe_only")
async def process_transcribe_only(
    file: UploadFile = File(...)
):
    """Nur transkribieren und formatierten Text zurueckgeben"""
    pdir = None
    try:
        set_progress("Upload läuft...", 10)
        
        project_id = "temp_" + str(uuid.uuid4())
        pdir = os.path.join(projects_dir, project_id)
        os.makedirs(pdir, exist_ok=True)
        
        base_name, file_ext = os.path.splitext(file.filename)
        safe_filename = re.sub(r'[^\w\s-]', '', base_name).strip().replace(" ", "_").replace("-", "_") + file_ext
        file_path = os.path.join(pdir, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        set_progress("Audio transkribieren...", 40)
        
        main_script = os.path.abspath(__file__)
        base_cmd = [sys.executable, "run_helper"] if getattr(sys, 'frozen', False) else [sys.executable, main_script, "run_helper"]
        
        subprocess.run(base_cmd + ["transcribe", file_path, "--edit-dir", pdir], cwd=base_dir, check=True)
        
        set_progress("Transkript formatieren...", 90)
        
        filename_no_ext = os.path.splitext(safe_filename)[0]
        transcript_path = os.path.join(pdir, "transcripts", f"{filename_no_ext}.json")
        
        if not os.path.exists(transcript_path):
            raise Exception("Transkription fehlgeschlagen: Keine JSON-Datei generiert.")
            
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
            
        # Parse and format text with speaker diarization
        formatted_text = ""
        current_speaker = None
        
        words = transcript_data.get("words", [])
        if words:
            for word in words:
                spk = word.get("speaker_id")
                # ignore audio_event if it doesn't have a speaker maybe, but elevenlabs usually has speaker_id
                if spk and spk != current_speaker:
                    if current_speaker is not None:
                        formatted_text += "\n\n"
                    spk_num = spk.replace('speaker_', '')
                    try:
                        spk_num = str(int(spk_num) + 1) # 1-indexed for readability
                    except ValueError:
                        pass
                    formatted_text += f"[Sprecher {spk_num}]:\n"
                    current_speaker = spk
                formatted_text += word.get("text", "")
        else:
            formatted_text = transcript_data.get("text", "")
            
        # Cleanup
        try:
            shutil.rmtree(pdir)
        except Exception:
            pass
            
        set_progress("Transkription abgeschlossen", 100, "success")
        
        return {
            "status": "success",
            "message": "Transkription erfolgreich!",
            "formatted_text": formatted_text.strip()
        }
        
    except Exception as e:
        if pdir and os.path.exists(pdir):
            try:
                shutil.rmtree(pdir)
            except Exception:
                pass
        import traceback
        traceback.print_exc()
        set_progress("Fehler bei Transkription", 0, "error")
        return {"status": "error", "message": str(e)}


@app.post("/api/render_final")
async def process_render_final(
    project_id: str = Form(...),
    transcript_json: str = Form(...),
    aiCut: bool = Form(False),
    subtitles: bool = Form(False),
    subtitle_style: str = Form("classic_bold"),
    highlight_color: str = Form("#00FFFF"),
    highlight_shape: str = Form("skew"),
    font_family: str = Form("'GT America', Helvetica, Arial, sans-serif"),
    font_weight: str = Form("bold"),
    text_case: str = Form("uppercase"),
    subtitle_language: str = Form("Original"),
    font_size: int = Form(20),
    y_position: int = Form(15),
    pill_radius: int = Form(20),
    shape_padding: int = Form(10),
    pop_in_animation: str = Form("true"),
    keep_punctuation: str = Form("false"),
    prompt: str = Form(""),
    custom_edl: str = Form("")
):
    """Step 2: Take edited transcript, generate EDL, and render"""
    try:
        set_progress("Speichere korrigiertes Transkript...", 10)
        
        pdir = os.path.join(projects_dir, project_id)
        if not os.path.exists(pdir):
            raise Exception("Projekt nicht gefunden.")
            
        with open(os.path.join(pdir, "project.json"), "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        filename = meta["filename"]
        filename_no_ext = meta["filename_no_ext"]
        
        transcript_path = os.path.join(pdir, "transcripts", f"{filename_no_ext}.json")
        file_path = os.path.join(pdir, filename)
        
        # Save edited transcript back to disk
        edited_transcript = json.loads(transcript_json)
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(edited_transcript, f, indent=2)
            
        set_progress("Packe Transkripte...", 20)
        main_script = os.path.abspath(__file__)
        base_cmd = [sys.executable, "run_helper"] if getattr(sys, 'frozen', False) else [sys.executable, main_script, "run_helper"]
        subprocess.run(base_cmd + ["pack_transcripts", "--edit-dir", pdir], cwd=base_dir, check=True)
        
        packed_path = os.path.join(pdir, "takes_packed.md")
        with open(packed_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()

        edl_json = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_video_name = f"final_{timestamp}.mp4"
        edl_path = os.path.join(pdir, "web_edl.json")
        
        if custom_edl:
            set_progress("Verwende angepassten Schnittplan...", 40)
            edl_json = json.loads(custom_edl)
            with open(edl_path, "w", encoding="utf-8") as f:
                json.dump(edl_json, f, indent=2)
        elif aiCut:
            set_progress("KI generiert perfekten Schnitt...", 40)
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            
            clean_file_path = file_path.replace('\\', '/')
            
            sys_prompt = f"""Du bist ein professioneller Video-Editor. 
            Hier ist ein gepacktes Transkript EINES EINZIGEN Videos:
            {transcript_text}
            
            Kundenwunsch: {prompt}
            
            Erstelle eine JSON EDL (Edit Decision List), die alle Versprecher, Pausen und Fehlversuche herausschneidet.
            Verwende NUR valides JSON.
            Es gibt nur EIN Video als Source. Der Source-Name MUSS exakt "{filename_no_ext}" lauten. UND LASS ALLE ANDEREN QUELLEN WEG!
            Format:
            {{
              "version": 1,
              "sources": {{ "{filename_no_ext}": "{clean_file_path}" }},
              "ranges": [
                {{ "source": "{filename_no_ext}", "start": 12.3, "end": 15.6, "beat": "Intro", "quote": "...", "reason": "..." }}
              ],
              "grade": "none",
              "subtitles": "edit/master.srt"
            }}
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=sys_prompt
            )
            
            match = re.search(r'```(?:json)?(.*?)```', response.text, re.DOTALL)
            json_str = match.group(1).strip() if match else response.text.strip()
            edl_json = json.loads(json_str)
            
            if "ranges" in edl_json:
                edl_json["ranges"] = [r for r in edl_json["ranges"] if r.get("source") == filename_no_ext]
                
            if "grade" in edl_json:
                edl_json["grade"] = "none"
                
            with open(edl_path, "w", encoding="utf-8") as f:
                json.dump(edl_json, f, indent=2)
        else:
            set_progress("Erstelle Timeline...", 40)
            duration = 0
            if edited_transcript.get("words"):
                duration = edited_transcript["words"][-1].get("end", 0) + 1.0
                
            edl_json = {
                "version": 1,
                "sources": { filename_no_ext: file_path.replace('\\', '/') },
                "ranges": [
                    { "source": filename_no_ext, "start": 0.0, "end": duration }
                ],
                "grade": "none",
                "subtitles": "edit/master.srt" if subtitles else ""
            }
            with open(edl_path, "w", encoding="utf-8") as f:
                json.dump(edl_json, f, indent=2)
                
        set_progress("Video wird gerendert...", 70)
        
        edl_abs = os.path.abspath(edl_path)
        main_script = os.path.abspath(__file__)
        base_cmd = [sys.executable, "run_helper"] if getattr(sys, 'frozen', False) else [sys.executable, main_script, "run_helper"]
        render_cmd = base_cmd + ["render", edl_abs, "-o", os.path.join(pdir, out_video_name)]
        
        if subtitles:
            render_cmd.append("--build-subtitles")
            render_cmd.extend(["--sub-style", subtitle_style])
            render_cmd.extend(["--highlight-color", highlight_color])
            render_cmd.extend(["--highlight-shape", highlight_shape])
            render_cmd.extend(["--font-family", font_family])
            render_cmd.extend(["--font-weight", font_weight])
            render_cmd.extend(["--text-case", text_case])
            render_cmd.extend(["--subtitle-language", subtitle_language])
            render_cmd.extend(["--font-size", str(font_size)])
            render_cmd.extend(["--y-position", str(y_position)])
            render_cmd.extend(["--pill-radius", str(pill_radius)])
            render_cmd.extend(["--shape-padding", str(shape_padding)])
            if pop_in_animation == "false":
                render_cmd.append("--disable-pop-in")
            if keep_punctuation == "true":
                render_cmd.append("--keep-punctuation")
            
        try:
            subprocess.run(render_cmd, cwd=base_dir, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as cpe:
            raise Exception(f"Render fehlgeschlagen: {cpe.stderr or cpe.stdout or str(cpe)}")
        
        # Update metadata to store final video path
        meta["final_video"] = out_video_name
        meta["status"] = "done"
        with open(os.path.join(pdir, "project.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        
        set_progress("Fertig!", 100, "success")

        return {
            "status": "success",
            "message": "Pipeline erfolgreich abgeschlossen!",
            "edl": edl_json,
            "video_url": f"http://localhost:8001/projects_files/{project_id}/{out_video_name}?t={timestamp}"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        set_progress("Fehler beim Rendern", 0, "error")
        return {"status": "error", "message": str(e)}

@app.get("/api/magic/voices")
async def get_magic_voices():
    """Fetch ElevenLabs voices"""
    try:
        from video_use_helpers import elevenlabs_tts
    except ImportError:
        import sys
        if getattr(sys, 'frozen', False):
            sys.path.append(os.path.join(sys._MEIPASS, "video-use", "helpers"))
        else:
            sys.path.append(os.path.join(base_dir, "video-use", "helpers"))
        import elevenlabs_tts
    
    voices = elevenlabs_tts.get_voices()
    return {"status": "success", "voices": voices}


@app.post("/api/magic/generate_script")
async def generate_magic_script(request: Request):
    """Generate script from prompt using Gemini"""
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        scene_count = body.get("scene_count", 5)
        scene_hints = body.get("scene_hints", [])
        
        if not prompt:
            raise Exception("Prompt is required")
            
        import sys
        if getattr(sys, 'frozen', False):
            sys.path.append(os.path.join(sys._MEIPASS, "video-use", "helpers"))
        else:
            sys.path.append(os.path.join(base_dir, "video-use", "helpers"))
        import magic_generator
        
        script = magic_generator.generate_script(prompt, scene_count, scene_hints)
        
        project_id = str(uuid.uuid4())
        pdir = os.path.join(projects_dir, project_id)
        os.makedirs(pdir, exist_ok=True)
        
        meta = {
            "id": project_id,
            "name": f"Magic: {prompt[:30]}...",
            "type": "magic",
            "status": "magic_draft",
            "created_at": datetime.now().isoformat()
        }
        with open(os.path.join(pdir, "project.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        with open(os.path.join(pdir, "magic_script.json"), "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2)
            
        return {"status": "success", "script": script, "project_id": project_id}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e)}

@app.post("/api/magic/save_draft")
async def save_magic_draft(
    project_id: str = Form(...),
    script_json: str = Form(...)
):
    try:
        pdir = os.path.join(projects_dir, project_id)
        if not os.path.exists(pdir):
            raise Exception("Project not found")
            
        script = json.loads(script_json)
        with open(os.path.join(pdir, "magic_script.json"), "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2)
            
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/magic/render_magic")
async def render_magic(
    script_json: str = Form(...),
    project_id: str = Form(None),
    voice_id: str = Form(...),
    subtitle_style: str = Form(...),
    highlight_color: str = Form(...),
    highlight_shape: str = Form(...),
    font_family: str = Form(...),
    font_weight: str = Form(...),
    text_case: str = Form(...),
    subtitle_language: str = Form("Original"),
    font_size: int = Form(20),
    y_position: int = Form(15),
    pill_radius: int = Form(20),
    shape_padding: int = Form(10),
    pop_in_animation: str = Form("true"),
    keep_punctuation: str = Form("false"),
    aspect_ratio: str = Form("9:16"),
    disable_subtitles: str = Form("false"),
    disable_hyperframes: str = Form("false"),
    motion_graphics_only: str = Form("false"),
    visual_style: str = Form("dynamic"),
    opener: UploadFile = File(None),
    closer: UploadFile = File(None),
    logo: UploadFile = File(None)
):
    """Generate and render the magic video from the approved script"""
    try:
        set_progress("Erstelle Magic Video Projekt...", 5)
        
        if project_id and os.path.exists(os.path.join(projects_dir, project_id)):
            pdir = os.path.join(projects_dir, project_id)
            pfile = os.path.join(pdir, "project.json")
            if os.path.exists(pfile):
                with open(pfile, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["status"] = "done"
                with open(pfile, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
        else:
            project_id = str(uuid.uuid4())
            pdir = os.path.join(projects_dir, project_id)
            os.makedirs(pdir, exist_ok=True)
            meta = {
                "id": project_id,
                "name": "Magic Project",
                "type": "magic",
                "status": "done",
                "created_at": datetime.now().isoformat()
            }
            with open(os.path.join(pdir, "project.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        
        script = json.loads(script_json)
        
        if opener:
            with open(os.path.join(pdir, "opener.mp4"), "wb") as f:
                f.write(await opener.read())
        if closer:
            with open(os.path.join(pdir, "closer.mp4"), "wb") as f:
                f.write(await closer.read())
        if logo:
            with open(os.path.join(pdir, "logo.png"), "wb") as f:
                f.write(await logo.read())
                
        set_progress("Generiere Voice-Over und KI-Visuals...", 15)
        
        import sys
        from pathlib import Path
        if getattr(sys, 'frozen', False):
            sys.path.append(os.path.join(sys._MEIPASS, "video-use", "helpers"))
        else:
            sys.path.append(os.path.join(base_dir, "video-use", "helpers"))
        import magic_generator
        
        edl = magic_generator.build_magic_project(
            project_dir=Path(pdir), 
            script_scenes=script, 
            voice_id=voice_id, 
            aspect_ratio=aspect_ratio, 
            disable_hyperframes=(disable_hyperframes.lower() == "true"),
            motion_graphics_only=(motion_graphics_only.lower() == "true"),
            visual_style=visual_style,
            progress_callback=set_progress
        )
        edl_path = Path(pdir) / "web_edl.json"
        
        # Save project metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_video_name = f"final_{timestamp}.mp4"
        final_path = os.path.join(pdir, out_video_name)
        meta = {
            "name": f"Magic {timestamp}",
            "filename_no_ext": f"magic_{timestamp}",
            "created_at": datetime.now().isoformat(),
            "status": "done",
            "final_video": out_video_name,
            "type": "magic"
        }
        with open(os.path.join(pdir, "project.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        set_progress("Rendere Untertitel und Effekte...", 60)
        
        main_script = os.path.abspath(__file__)
        base_cmd = [sys.executable, "run_helper"] if getattr(sys, 'frozen', False) else [sys.executable, main_script, "run_helper"]
        args = base_cmd + [
            "render",
            str(edl_path),
            "-o",
            str(final_path)
        ]
        
        if disable_subtitles.lower() != "true":
            args.extend([
                "--build-subtitles",
                "--sub-style", subtitle_style,
                "--highlight-color", highlight_color,
                "--highlight-shape", highlight_shape,
                "--font-family", font_family,
                "--font-weight", font_weight,
                "--text-case", text_case,
                "--subtitle-language", subtitle_language,
                "--font-size", str(font_size),
                "--y-position", str(y_position),
                "--pill-radius", str(pill_radius),
                "--shape-padding", str(shape_padding)
            ])
            if pop_in_animation == "false":
                args.append("--disable-pop-in")
            if keep_punctuation == "true":
                args.append("--keep-punctuation")
            
        print("Running helper command:", args)
        subprocess.run(args, cwd=base_dir, check=True)
        
        set_progress("Magic Video fertig!", 100, "success")
        
        return {
            "status": "success",
            "message": "Magic Video erfolgreich erstellt!",
            "project_id": project_id,
            "video_url": f"http://localhost:8001/projects_files/{project_id}/{out_video_name}?t={timestamp}"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        set_progress("Fehler beim Magic Render", 0, "error")
        return {"status": "error", "message": str(e)}

# Serve React Frontend (SPA fallback)
frontend_dist = os.path.join(base_dir, "web-ui", "frontend", "dist")
if getattr(sys, 'frozen', False):
    frontend_dist = os.path.join(sys._MEIPASS, "frontend_dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Serve any static file in root if it exists
        possible_file = os.path.join(frontend_dist, full_path)
        if os.path.isfile(possible_file):
            return FileResponse(possible_file)
            
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return {"error": "Frontend not found"}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_helper":
        helper_name = sys.argv[2]
        sys.argv = [sys.argv[0]] + sys.argv[3:]
        import runpy
        if getattr(sys, 'frozen', False):
            helper_path = os.path.join(sys._MEIPASS, "video-use", "helpers", helper_name + ".py")
        else:
            helper_path = os.path.join(base_dir, "video-use", "helpers", helper_name + ".py")
            
        runpy.run_path(helper_path, run_name="__main__")
        sys.exit(0)

    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
