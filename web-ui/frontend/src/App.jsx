import { useState, useEffect } from 'react';
import './App.css';
import { useAuth } from './contexts/AuthContext';
import ProgressOverlay from './components/ProgressOverlay';
import TranscriptEditor from './components/TranscriptEditor';
import StyleSelector from './components/StyleSelector';

function EdlEditor({ edl, onSave }) {
  if (!edl || !edl.ranges || edl.ranges.length === 0) return null;
  const [localEdl, setLocalEdl] = useState(JSON.parse(JSON.stringify(edl)));

  const updateRange = (index, field, delta) => {
    const newEdl = { ...localEdl };
    const val = newEdl.ranges[index][field];
    newEdl.ranges[index][field] = parseFloat((val + delta).toFixed(2));
    setLocalEdl(newEdl);
  };

  const removeRange = (index) => {
    if (!window.confirm("Diesen Schnitt wirklich entfernen?")) return;
    const newEdl = { ...localEdl };
    newEdl.ranges.splice(index, 1);
    setLocalEdl(newEdl);
  };

  return (
    <div className="card" style={{borderLeft: '6px solid #ff7b00'}}>
      <h3 style={{marginTop: 0, color: '#ff7b00', textTransform: 'uppercase'}}>Schnitt-Feintuning (EDL)</h3>
      <p style={{fontSize: '0.9rem', color: '#666', marginBottom: '20px'}}>Passe die Start- und Endzeiten der KI-Schnitte an.</p>
      
      <div style={{maxHeight: '400px', overflowY: 'auto', paddingRight: '10px'}}>
        {localEdl.ranges.map((r, i) => (
          <div key={i} style={{marginBottom: '15px', padding: '15px', background: '#f9f9fa', borderRadius: '8px', border: '1px solid #e4e4e7', position: 'relative'}}>
            <button 
              onClick={() => removeRange(i)}
              style={{position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem'}}
              title="Schnitt entfernen"
            >
              🗑️
            </button>
            <div style={{fontWeight: 'bold', marginBottom: '8px', color: '#3333CC'}}>Schnitt {i+1}</div>
            {r.quote && <div style={{fontSize: '0.9rem', fontStyle: 'italic', marginBottom: '12px', color: '#555', paddingRight: '20px'}}>"{r.quote}"</div>}
            
            <div style={{display: 'flex', flexDirection: 'column', gap: '10px'}}>
              <div style={{display: 'flex', flexWrap: 'wrap', gap: '15px', alignItems: 'center'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '5px'}}>
                  <span style={{width: '40px', fontWeight: '600'}}>Start:</span>
                  <button onClick={() => updateRange(i, 'start', -0.1)} style={{padding: '4px 10px', background: '#e4e4e7', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>-0.1s</button>
                  <input type="number" step="0.1" value={r.start} onChange={(e) => {
                     const newEdl = {...localEdl};
                     newEdl.ranges[i].start = parseFloat(e.target.value) || 0;
                     setLocalEdl(newEdl);
                  }} style={{width: '70px', textAlign: 'center', padding: '4px', border: '1px solid #ccc', borderRadius: '4px'}} />
                  <button onClick={() => updateRange(i, 'start', 0.1)} style={{padding: '4px 10px', background: '#e4e4e7', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>+0.1s</button>
                </div>
                
                <div style={{display: 'flex', alignItems: 'center', gap: '5px'}}>
                  <span style={{width: '40px', fontWeight: '600'}}>Ende:</span>
                  <button onClick={() => updateRange(i, 'end', -0.1)} style={{padding: '4px 10px', background: '#e4e4e7', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>-0.1s</button>
                  <input type="number" step="0.1" value={r.end} onChange={(e) => {
                     const newEdl = {...localEdl};
                     newEdl.ranges[i].end = parseFloat(e.target.value) || 0;
                     setLocalEdl(newEdl);
                  }} style={{width: '70px', textAlign: 'center', padding: '4px', border: '1px solid #ccc', borderRadius: '4px'}} />
                  <button onClick={() => updateRange(i, 'end', 0.1)} style={{padding: '4px 10px', background: '#e4e4e7', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>+0.1s</button>
                </div>
              </div>

              <div style={{display: 'flex', alignItems: 'center', gap: '5px', marginTop: '5px'}}>
                <span style={{fontWeight: '600', fontSize: '0.85rem', color: '#666'}}>Subtitles Höhe (Y-Pos):</span>
                <select value={r.y_position_override || ""} onChange={(e) => {
                   const newEdl = {...localEdl};
                   newEdl.ranges[i].y_position_override = e.target.value ? Number(e.target.value) : null;
                   setLocalEdl(newEdl);
                }} style={{width: '130px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px'}}>
                  <option value="">Standard</option>
                  <option value="15">Unten</option>
                  <option value="30">Mitte-Unten</option>
                  <option value="50">Mitte</option>
                  <option value="75">Oben</option>
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button className="magic-button" style={{marginTop: '20px'}} onClick={() => onSave(localEdl)}>
        Mit angepasstem Timing neu rendern
      </button>
    </div>
  );
}

function LoginScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await signIn(email, password);
    if (res.error) setError(res.error.message);
  };

  return (
    <div className="login-container">
      <div className="card login-card">
        <h2>Login (labs-api)</h2>
        <form onSubmit={handleSubmit}>
          <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
          <input type="password" placeholder="Passwort" value={password} onChange={e => setPassword(e.target.value)} required />
          <button type="submit" className="magic-button">Einloggen</button>
        </form>
        {error && <p className="error-text">{error}</p>}
      </div>
    </div>
  );
}

function MainDashboard() {
  const { user, signOut } = useAuth();
  
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [file, setFile] = useState(null);
  const [promptStr, setPromptStr] = useState("");
  const [options, setOptions] = useState({
    aiCut: true,
    subtitles: true
  });
  
  // Pipeline state
  const [pipelineState, setPipelineState] = useState("dashboard");
  const [transcriptData, setTranscriptData] = useState(null);
  
  // Font and Style state (DMAX Style)
  const [selectedStyle, setSelectedStyle] = useState("tiktok_dynamic");
  const [highlightColor, setHighlightColor] = useState("#ff6400");
  const [highlightShape, setHighlightShape] = useState("rounded");
  const [fontFamily, setFontFamily] = useState("'Proxima Nova', sans-serif");
  const [fontWeight, setFontWeight] = useState("bold");
  const [textCase, setTextCase] = useState("uppercase");
  const [fontSize, setFontSize] = useState(10);
  const [yPosition, setYPosition] = useState(10);
  const [pillRadius, setPillRadius] = useState(10);
  const [shapePadding, setShapePadding] = useState(5);
  const [popInAnimation, setPopInAnimation] = useState(true);
  const [keepPunctuation, setKeepPunctuation] = useState(false);
  const [subtitleLanguage, setSubtitleLanguage] = useState("Original");
  const [disableSubtitles, setDisableSubtitles] = useState(false);
  const [disableHyperframes, setDisableHyperframes] = useState(false);
  const [motionGraphicsOnly, setMotionGraphicsOnly] = useState(false);
  const [visualStyle, setVisualStyle] = useState("dynamic");
  
  // Assets state
  const [openerFile, setOpenerFile] = useState(null);
  const [closerFile, setCloserFile] = useState(null);
  const [logoFile, setLogoFile] = useState(null);

  // Transcribe-only state
  const [transcribeOnlyResult, setTranscribeOnlyResult] = useState("");

  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [magicVoices, setMagicVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState("TaCvaiAKYmcOVUiSkDM3"); // Default voice
  const [magicScript, setMagicScript] = useState(null);
  const [sceneCount, setSceneCount] = useState(5);
  const [sceneHints, setSceneHints] = useState([""]);
  const [aspectRatio, setAspectRatio] = useState("9:16");

  const [showSettings, setShowSettings] = useState(false);
  const [settingsKeys, setSettingsKeys] = useState({ gemini_api_key: "", elevenlabs_api_key: "" });

  const loadSettings = async () => {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      setSettingsKeys(data);
    } catch(err) { console.error("Failed to load settings"); }
  };

  const saveSettings = async () => {
    try {
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settingsKeys)
      });
      setShowSettings(false);
    } catch(err) { console.error("Failed to save settings"); }
  };

  const handleAddHint = () => setSceneHints([...sceneHints, ""]);
  const handleHintChange = (i, val) => {
    const newHints = [...sceneHints];
    newHints[i] = val;
    setSceneHints(newHints);
  };

  const loadProjects = async () => {
    try {
      const res = await fetch("/api/projects");
      const data = await res.json();
      if (data.status === "success") {
        setProjects(data.projects);
      }
    } catch(err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (pipelineState === "dashboard") {
      loadProjects();
    }
  }, [pipelineState]);

  useEffect(() => {
    // Load voices
    fetch("/api/magic/voices")
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          setMagicVoices(data.voices);
        }
      })
      .catch(err => console.error(err));
  }, []);

  const handleRename = async (id, oldName) => {
    const newName = window.prompt("Neuer Projektname:", oldName);
    if (!newName || newName === oldName) return;
    try {
      await fetch(`/api/projects/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName })
      });
      loadProjects();
    } catch(err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Projekt wirklich endgültig löschen?")) return;
    try {
      await fetch(`/api/projects/${id}`, { method: "DELETE" });
      loadProjects();
    } catch(err) {
      console.error(err);
    }
  };

  const handleOpenProject = async (id) => {
    try {
      const res = await fetch(`/api/projects/${id}`);
      const data = await res.json();
      if (data.status === "success") {
        setProjectId(id);
        
        if (data.project.type === "magic") {
           setMagicScript(data.transcript);
           if (data.project.status === "done" && data.project.final_video) {
              setResult({
                 edl: {},
                 video_url: `/projects_files/${id}/${data.project.final_video}?t=${Date.now()}`
              });
              setPipelineState("done");
           } else {
              setPipelineState("magic_script_review");
           }
        } else {
           setTranscriptData(data.transcript);
           if (data.project.status === "done" && data.project.final_video) {
              setResult({
                 edl: {},
                 video_url: `/projects_files/${id}/${data.project.final_video}?t=${Date.now()}`
              });
              setPipelineState("done");
           } else {
              setPipelineState("editing");
           }
        }
      }
    } catch(err) {
      console.error(err);
      setErrorMsg("Projekt konnte nicht geladen werden.");
    }
  };

  const handleOptionChange = (e) => {
    setOptions({ ...options, [e.target.name]: e.target.checked });
  };

  const handleUploadAndTranscribe = async (e) => {
    e.preventDefault();
    if (!file) return alert("Bitte ein Video auswählen!");

    setPipelineState("uploading");
    setErrorMsg("");

    const formData = new FormData();
    formData.append("file", file);
    if (openerFile) formData.append("opener", openerFile);
    if (closerFile) formData.append("closer", closerFile);
    if (logoFile) formData.append("logo", logoFile);

    try {
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setProjectId(data.project_id);
        setTranscriptData(data.transcript);
        setPipelineState("editing");
      } else {
        setErrorMsg(`❌ Backend-Fehler: ${data.message}`);
        setPipelineState("new_project");
      }
    } catch (error) {
      setErrorMsg("❌ Netzwerkfehler zum Backend.");
      setPipelineState("new_project");
    }
  };

  const handleTranscribeOnlySubmit = async (e) => {
    e.preventDefault();
    if (!file) return alert("Bitte ein Video auswählen!");

    setPipelineState("uploading");
    setErrorMsg("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/transcribe_only", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setTranscribeOnlyResult(data.formatted_text);
        setPipelineState("transcribe_result");
      } else {
        setErrorMsg(`❌ Backend-Fehler: ${data.message}`);
        setPipelineState("transcribe_only");
      }
    } catch (error) {
      setErrorMsg("❌ Netzwerkfehler zum Backend.");
      setPipelineState("transcribe_only");
    }
  };

  const handleRenderFinal = async (editedTranscript) => {
    setPipelineState("rendering");
    setErrorMsg("");

    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("transcript_json", JSON.stringify(editedTranscript));
    formData.append("aiCut", options.aiCut);
    formData.append("subtitles", options.subtitles);
    formData.append("subtitle_style", selectedStyle);
    formData.append("highlight_color", highlightColor);
    formData.append("highlight_shape", highlightShape);
    formData.append("font_family", fontFamily);
    formData.append("font_weight", fontWeight);
    formData.append("text_case", textCase);
    formData.append("subtitle_language", subtitleLanguage);
    formData.append("font_size", fontSize);
    formData.append("y_position", yPosition);
    formData.append("pill_radius", pillRadius);
    formData.append("shape_padding", shapePadding);
    formData.append("pop_in_animation", popInAnimation ? "true" : "false");
    formData.append("keep_punctuation", keepPunctuation ? "true" : "false");
    formData.append("prompt", promptStr);

    try {
      const response = await fetch("/api/render_final", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setResult(data);
        setPipelineState("done");
      } else {
        setErrorMsg(`❌ Backend-Fehler: ${data.message}`);
        setPipelineState("editing");
      }
    } catch (error) {
      setErrorMsg("❌ Netzwerkfehler zum Backend.");
      setPipelineState("editing");
    }
  };

  const handleRenderCustomEdl = async (modifiedEdl) => {
    setPipelineState("rendering");
    setErrorMsg("");

    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("transcript_json", JSON.stringify(transcriptData));
    formData.append("aiCut", options.aiCut);
    formData.append("subtitles", options.subtitles);
    formData.append("subtitle_style", selectedStyle);
    formData.append("highlight_color", highlightColor);
    formData.append("highlight_shape", highlightShape);
    formData.append("font_family", fontFamily);
    formData.append("font_weight", fontWeight);
    formData.append("text_case", textCase);
    formData.append("subtitle_language", subtitleLanguage);
    formData.append("font_size", fontSize);
    formData.append("y_position", yPosition);
    formData.append("pill_radius", pillRadius);
    formData.append("shape_padding", shapePadding);
    formData.append("pop_in_animation", popInAnimation ? "true" : "false");
    formData.append("keep_punctuation", keepPunctuation ? "true" : "false");
    formData.append("prompt", promptStr);
    formData.append("custom_edl", JSON.stringify(modifiedEdl));

    try {
      const response = await fetch("/api/render_final", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setResult(data);
        setPipelineState("done");
      } else {
        setErrorMsg(`❌ Backend-Fehler: ${data.message}`);
        setPipelineState("done");
      }
    } catch (error) {
      setErrorMsg("❌ Netzwerkfehler zum Backend.");
      setPipelineState("done");
    }
  };

  const handleGenerateScript = async (e) => {
    e.preventDefault();
    if (!promptStr) return alert("Bitte ein Thema eingeben!");

    setPipelineState("uploading"); // Reusing uploading state for progress overlay
    setErrorMsg("");

    try {
      const response = await fetch("/api/magic/generate_script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
           prompt: promptStr,
           scene_count: sceneCount,
           scene_hints: sceneHints.filter(h => h.trim() !== ""),
           aspect_ratio: aspectRatio
        })
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setProjectId(data.project_id);
        setMagicScript(data.script);
        setPipelineState("magic_script_review");
      } else {
        setErrorMsg(`❌ Script-Fehler: ${data.message}`);
        setPipelineState("new_magic");
      }
    } catch (error) {
      setErrorMsg("❌ Netzwerkfehler zum Backend.");
      setPipelineState("new_magic");
    }
  };

  const handleSaveDraft = async () => {
    if (!projectId) return;
    try {
      const formData = new FormData();
      formData.append("project_id", projectId);
      formData.append("script_json", JSON.stringify(magicScript));
      const response = await fetch("/api/magic/save_draft", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      if (data.status === "success") {
        alert("Entwurf erfolgreich gespeichert!");
      } else {
        alert("Fehler beim Speichern: " + data.message);
      }
    } catch (err) {
      alert("Netzwerkfehler beim Speichern.");
    }
  };

  const handleRenderMagic = async () => {
    setPipelineState("rendering");
    setErrorMsg("");

    const formData = new FormData();
    formData.append("script_json", JSON.stringify(magicScript));
    if (projectId) formData.append("project_id", projectId);
    formData.append("voice_id", selectedVoice);
    formData.append("subtitle_style", selectedStyle);
    formData.append("highlight_color", highlightColor);
    formData.append("highlight_shape", highlightShape);
    formData.append("font_family", fontFamily);
    formData.append("font_weight", fontWeight);
    formData.append("text_case", textCase);
    formData.append("subtitle_language", subtitleLanguage);
    formData.append("font_size", fontSize);
    formData.append("y_position", yPosition);
    formData.append("pill_radius", pillRadius);
    formData.append("shape_padding", shapePadding);
    formData.append("pop_in_animation", popInAnimation ? "true" : "false");
    formData.append("keep_punctuation", keepPunctuation ? "true" : "false");
    formData.append("aspect_ratio", aspectRatio);
    if (disableSubtitles) formData.append("disable_subtitles", "true");
    if (disableHyperframes) formData.append("disable_hyperframes", "true");
    if (motionGraphicsOnly) formData.append("motion_graphics_only", "true");
    formData.append("visual_style", visualStyle);
    
    if (openerFile) formData.append("opener", openerFile);
    if (closerFile) formData.append("closer", closerFile);
    if (logoFile) formData.append("logo", logoFile);

    try {
      const response = await fetch("/api/magic/render_magic", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setProjectId(data.project_id);
        setResult(data);
        setPipelineState("done");
      } else {
        setErrorMsg(`❌ Backend-Fehler: ${data.message}`);
        setPipelineState("magic_script_review");
      }
    } catch (error) {
      setErrorMsg("❌ Netzwerkfehler zum Backend.");
      setPipelineState("magic_script_review");
    }
  };

  return (
    <>
      <ProgressOverlay 
        isVisible={pipelineState === "uploading" || pipelineState === "rendering"} 
        statusText={pipelineState === "uploading" ? "✨ LADE & TRANSKRIBIERE..." : "✨ KI SCHNEIDET & RENDERT..."}
      />
      
      <header>
        <h1 onClick={() => setPipelineState("dashboard")} style={{cursor: 'pointer'}}>VIDEOMAGIC <span>STUDIO</span></h1>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <p className="subtitle">by Pixelschickeria</p>
          <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
            <button 
              onClick={() => { setShowSettings(true); loadSettings(); }} 
              style={{background: 'none', border: '1px solid #ccc', color: '#333', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}
            >
              ⚙️ Settings
            </button>
            <span style={{marginRight: '15px', fontWeight: '600'}}>{user.email}</span>
            <button onClick={signOut} style={{background: '#3333CC', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>Logout</button>
          </div>
        </div>
      </header>

      {showSettings && (
        <div className="modal-overlay" style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <div className="modal-content" style={{background: '#fff', padding: '30px', borderRadius: '12px', width: '500px', maxWidth: '90%'}}>
            <h2 style={{marginTop: 0, color: '#3333CC'}}>⚙️ API Settings</h2>
            <p style={{fontSize: '0.9rem', color: '#666', marginBottom: '20px'}}>
              Hinterlege hier deine API-Schlüssel. Diese werden lokal auf deinem PC gespeichert.
            </p>
            
            <div style={{marginBottom: '15px'}}>
              <label style={{display: 'block', fontWeight: 'bold', marginBottom: '5px'}}>Gemini API Key (Für KI-Skripte & Prompts):</label>
              <input 
                type="password" 
                value={settingsKeys.gemini_api_key} 
                onChange={(e) => setSettingsKeys({...settingsKeys, gemini_api_key: e.target.value})}
                style={{width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc'}}
                placeholder="AIzaSy..."
              />
            </div>

            <div style={{marginBottom: '25px'}}>
              <label style={{display: 'block', fontWeight: 'bold', marginBottom: '5px'}}>ElevenLabs API Key (Für Voice-Over):</label>
              <input 
                type="password" 
                value={settingsKeys.elevenlabs_api_key} 
                onChange={(e) => setSettingsKeys({...settingsKeys, elevenlabs_api_key: e.target.value})}
                style={{width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc'}}
                placeholder="sk_..."
              />
            </div>

            <div style={{display: 'flex', gap: '10px', justifyContent: 'flex-end'}}>
              <button onClick={() => setShowSettings(false)} style={{padding: '10px 20px', background: '#ccc', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>Abbrechen</button>
              <button onClick={saveSettings} style={{padding: '10px 20px', background: '#3333CC', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>Speichern</button>
            </div>
          </div>
        </div>
      )}

      <main>
        {errorMsg && <div className="status-box" style={{backgroundColor: '#ff4444', color: 'white'}}>{errorMsg}</div>}

        {pipelineState === "dashboard" && (
           <div className="dashboard">
             <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', flexWrap: 'wrap', gap: '10px'}}>
               <h2>Projekt-Übersicht</h2>
               <div style={{display: 'flex', gap: '10px'}}>
                 <button className="magic-button" onClick={() => { setFile(null); setPipelineState("new_project"); }} style={{padding: '10px 20px', fontSize: '1rem', background: '#333'}}>
                    + Video verpacken (Classic)
                 </button>
                 <button className="magic-button" onClick={() => { setPromptStr(""); setPipelineState("new_magic"); }} style={{padding: '10px 20px', fontSize: '1rem'}}>
                    ✨ Magic Generator
                 </button>
                 <button className="magic-button" onClick={() => { setFile(null); setTranscribeOnlyResult(""); setPipelineState("transcribe_only"); }} style={{padding: '10px 20px', fontSize: '1rem', background: '#008080'}}>
                    📝 Nur Transkript erstellen
                 </button>
               </div>
             </div>

             {projects.length === 0 ? (
               <p style={{textAlign: 'center', color: '#999'}}>Noch keine Projekte vorhanden. Starte jetzt dein erstes!</p>
             ) : (
               <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px'}}>
                 {projects.map(p => (
                   <div key={p.id} className="card" style={{padding: '20px'}}>
                     <h3 style={{margin: '0 0 10px 0', fontSize: '1.2rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{p.name}</h3>
                     <p style={{color: '#999', fontSize: '0.8rem', marginBottom: '20px'}}>
                       Erstellt: {new Date(p.created_at).toLocaleString()}
                     </p>
                     <div style={{display: 'flex', gap: '10px', flexWrap: 'wrap'}}>
                       <button onClick={() => handleOpenProject(p.id)} style={{flex: 1, padding: '8px', background: '#3333CC', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>Öffnen</button>
                       <button onClick={() => handleRename(p.id, p.name)} style={{flex: 1, padding: '8px', background: '#333', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>Umbenennen</button>
                       <button onClick={() => handleDelete(p.id)} style={{width: '100%', padding: '8px', background: '#CC3333', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>Löschen</button>
                     </div>
                   </div>
                 ))}
               </div>
             )}
           </div>
        )}

        {pipelineState === "new_project" && (
          <form onSubmit={handleUploadAndTranscribe} className="upload-form">
            <div className="card">
              <h2>1. Video auswählen</h2>
              <input 
                type="file" 
                accept="video/mp4,video/quicktime" 
                onChange={(e) => setFile(e.target.files[0])} 
                className="file-input"
              />
            </div>
            
            <div className="card">
              <h2>2. Assets hinzufügen (Optional)</h2>
              <div style={{display: 'flex', flexDirection: 'column', gap: '15px'}}>
                <div>
                  <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Video Opener (MP4/MOV)</label>
                  <input type="file" accept="video/mp4,video/quicktime" onChange={(e) => setOpenerFile(e.target.files[0])} className="file-input" style={{padding: '5px'}} />
                </div>
                <div>
                  <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Video Closer (MP4/MOV)</label>
                  <input type="file" accept="video/mp4,video/quicktime" onChange={(e) => setCloserFile(e.target.files[0])} className="file-input" style={{padding: '5px'}} />
                </div>
                <div>
                  <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Logo-Bug / Wasserzeichen (PNG mit Transparenz)</label>
                  <input type="file" accept="image/png" onChange={(e) => setLogoFile(e.target.files[0])} className="file-input" style={{padding: '5px'}} />
                </div>
              </div>
            </div>

            <div className="card">
              <h2>3. Workflows aktivieren</h2>
              <div className="checkbox-group">
                <label>
                  <input type="checkbox" name="aiCut" checked={options.aiCut} onChange={handleOptionChange} />
                  <span>KI-Schnitt (Versprecher/Pausen entfernen)</span>
                </label>
                <label>
                  <input type="checkbox" name="subtitles" checked={options.subtitles} onChange={handleOptionChange} />
                  <span>Untertitel generieren</span>
                </label>
              </div>
            </div>
            <div className="card">
              <h2>4. KI-Regieanweisung (Optional)</h2>
              <textarea 
                placeholder="z.B. Mach den Schnitt knackig und entferne alle Füllwörter..."
                value={promptStr}
                onChange={(e) => setPromptStr(e.target.value)}
                rows="3"
              ></textarea>
            </div>
            <button type="submit" className="magic-button">
              Projekt erstellen & Video analysieren
            </button>
            <div style={{textAlign: 'center', marginTop: '15px'}}>
               <button type="button" onClick={() => setPipelineState("dashboard")} style={{background: 'none', border: 'none', color: '#999', cursor: 'pointer', textDecoration: 'underline'}}>
                 Abbrechen & zurück zum Dashboard
               </button>
            </div>
          </form>
        )}

        {pipelineState === "new_magic" && (
          <form onSubmit={handleGenerateScript} className="upload-form">
            <div className="card">
              <h2>✨ 1. Worum soll es in dem Video gehen?</h2>
              <textarea 
                autoFocus
                placeholder="z.B. Erkläre schwarze Löcher für Anfänger in einfachen Worten..."
                value={promptStr}
                onChange={(e) => setPromptStr(e.target.value)}
                rows="4"
                required
              ></textarea>
            </div>
            
            <div className="card">
              <h2>2. Video-Format</h2>
              <div style={{display: 'flex', gap: '20px'}}>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '1.1rem'}}>
                  <input type="radio" name="aspectRatio" value="9:16" checked={aspectRatio === "9:16"} onChange={(e) => setAspectRatio(e.target.value)} />
                  📱 Hochformat (9:16 - TikTok, Reels, Shorts)
                </label>
                <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '1.1rem'}}>
                  <input type="radio" name="aspectRatio" value="16:9" checked={aspectRatio === "16:9"} onChange={(e) => setAspectRatio(e.target.value)} />
                  🖥️ Querformat (16:9 - YouTube, TV)
                </label>
              </div>
            </div>

            <div className="card">
              <h2>3. Szenen-Anzahl & Vorgaben</h2>
              <div style={{marginBottom: '15px'}}>
                <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Anzahl der Szenen (Slides):</label>
                <input type="number" min="1" max="20" value={sceneCount} onChange={(e) => setSceneCount(parseInt(e.target.value) || 5)} className="file-input" style={{padding: '5px', width: '100px'}} />
              </div>
              <div>
                <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Optional: Inhaltsangabe pro Szene</label>
                <p style={{fontSize: '0.85rem', color: '#666', marginTop: 0}}>Wenn du genaue Vorstellungen hast, was in einer Szene passieren soll, schreibe es hier hin:</p>
                {sceneHints.map((hint, i) => (
                  <div key={i} style={{marginBottom: '10px', display: 'flex', gap: '10px', alignItems: 'center'}}>
                    <span style={{fontWeight: 'bold', color: '#ff7b00', width: '70px'}}>Szene {i+1}:</span>
                    <input type="text" placeholder={`Idee für Szene ${i+1}...`} value={hint} onChange={(e) => handleHintChange(i, e.target.value)} style={{flex: 1, padding: '8px', border: '1px solid #ccc', borderRadius: '4px'}} />
                  </div>
                ))}
                {sceneHints.length < sceneCount && (
                  <button type="button" onClick={handleAddHint} style={{background: '#eee', border: '1px solid #ccc', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.9rem', marginTop: '10px'}}>+ Weitere Szene beschreiben</button>
                )}
              </div>
            </div>

            <div className="card">
              <h2>4. Stimme auswählen (ElevenLabs)</h2>
              <select value={selectedVoice} onChange={(e) => setSelectedVoice(e.target.value)} className="file-input" style={{padding: '10px', fontSize: '1rem'}}>
                {magicVoices.map(v => (
                  <option key={v.voice_id} value={v.voice_id}>{v.name}</option>
                ))}
              </select>
            </div>

            <div className="card">
              <h2>5. Assets hinzufügen (Optional)</h2>
              <div style={{display: 'flex', flexDirection: 'column', gap: '15px'}}>
                <div>
                  <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Video Opener (MP4/MOV)</label>
                  <input type="file" accept="video/mp4,video/quicktime" onChange={(e) => setOpenerFile(e.target.files[0])} className="file-input" style={{padding: '5px'}} />
                </div>
                <div>
                  <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Video Closer (MP4/MOV)</label>
                  <input type="file" accept="video/mp4,video/quicktime" onChange={(e) => setCloserFile(e.target.files[0])} className="file-input" style={{padding: '5px'}} />
                </div>
                <div>
                  <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>Logo-Bug (PNG mit Transparenz)</label>
                  <input type="file" accept="image/png" onChange={(e) => setLogoFile(e.target.files[0])} className="file-input" style={{padding: '5px'}} />
                </div>
              </div>
            </div>

            <button type="submit" className="magic-button">
              Skript & Bild-Prompts generieren
            </button>
            <div style={{textAlign: 'center', marginTop: '15px'}}>
               <button type="button" onClick={() => setPipelineState("dashboard")} style={{background: 'none', border: 'none', color: '#999', cursor: 'pointer', textDecoration: 'underline'}}>
                 Abbrechen
               </button>
             </div>
           </form>
        )}

        {pipelineState === "transcribe_only" && (
          <form onSubmit={handleTranscribeOnlySubmit} className="upload-form">
            <div className="card">
              <h2>📝 Video für Transkript auswählen</h2>
              <p style={{color: '#666', marginBottom: '20px'}}>Lade ein Video hoch. Die KI erstellt ein reines Text-Transkript, welches du als .txt speichern oder als PDF drucken kannst.</p>
              <input 
                type="file" 
                accept="video/mp4,video/quicktime,audio/mp3,audio/wav" 
                onChange={(e) => setFile(e.target.files[0])} 
                className="file-input"
              />
            </div>
            <button type="submit" className="magic-button" style={{background: '#008080'}}>
              Video transkribieren
            </button>
            <div style={{textAlign: 'center', marginTop: '15px'}}>
               <button type="button" onClick={() => setPipelineState("dashboard")} style={{background: 'none', border: 'none', color: '#999', cursor: 'pointer', textDecoration: 'underline'}}>
                 Abbrechen & zurück zum Dashboard
               </button>
            </div>
          </form>
        )}

        {pipelineState === "transcribe_result" && (
          <div className="card printable-area">
            <h2>📝 Fertiges Transkript</h2>
            <div style={{display: 'flex', gap: '15px', marginBottom: '20px'}} className="no-print">
              <button 
                onClick={() => {
                  const blob = new Blob([transcribeOnlyResult], { type: "text/plain;charset=utf-8" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = file ? `${file.name}_transcript.txt` : "transcript.txt";
                  a.click();
                  URL.revokeObjectURL(url);
                }} 
                className="magic-button" 
                style={{background: '#333'}}
              >
                💾 Als .txt herunterladen
              </button>
              <button 
                onClick={() => window.print()} 
                className="magic-button" 
                style={{background: '#008080'}}
              >
                🖨️ Drucken / Als PDF speichern
              </button>
            </div>
            
            <textarea 
              value={transcribeOnlyResult} 
              onChange={(e) => setTranscribeOnlyResult(e.target.value)}
              className="transcript-textarea"
              style={{width: '100%', minHeight: '400px', padding: '15px', fontFamily: 'monospace', fontSize: '1rem', borderRadius: '8px', border: '1px solid #ccc', resize: 'vertical'}}
            />

            <div style={{textAlign: 'center', marginTop: '20px'}} className="no-print">
               <button type="button" onClick={() => setPipelineState("dashboard")} style={{background: 'none', border: 'none', color: '#3333CC', cursor: 'pointer', textDecoration: 'underline', fontWeight: 'bold'}}>
                 Zurück zum Dashboard
               </button>
            </div>
          </div>
        )}

        {pipelineState === "magic_script_review" && (
          <div>
            <div className="card" style={{borderLeft: '6px solid #3333CC'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
                <div>
                  <h2 style={{margin: 0}}>Skript-Vorschau</h2>
                  <p style={{color: '#666', margin: '5px 0 0 0'}}>Hier ist das generierte Skript für die KI-Stimme und die Bilder. Du kannst es direkt bearbeiten!</p>
                </div>
                <button onClick={handleSaveDraft} style={{background: '#333', color: '#fff', padding: '8px 16px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>
                  💾 Entwurf speichern
                </button>
              </div>
              
              {magicScript && magicScript.map((scene, i) => (
                <div key={i} style={{marginBottom: '20px', padding: '15px', background: '#f9f9fa', borderRadius: '8px', border: '1px solid #ddd'}}>
                  <h3 style={{marginTop: 0}}>Szene {i + 1}</h3>
                  <div style={{marginBottom: '10px'}}>
                    <label style={{fontWeight: 'bold', fontSize: '0.9rem', color: '#ff7b00'}}>KI-Stimme sagt:</label>
                    <textarea 
                      autoFocus={i === 0}
                      value={scene.speech}
                      onChange={(e) => {
                        const newScript = [...magicScript];
                        newScript[i].speech = e.target.value;
                        setMagicScript(newScript);
                      }}
                      rows="3"
                    ></textarea>
                  </div>
                  <div style={{display: 'flex', gap: '20px'}}>
                    <div style={{flex: 1}}>
                      <label style={{fontWeight: 'bold', fontSize: '0.9rem', color: '#3333CC'}}>KI-Bild (Imagen 4 Prompt):</label>
                      <textarea 
                        value={scene.visual_prompt}
                        onChange={(e) => {
                          const newScript = [...magicScript];
                          newScript[i].visual_prompt = e.target.value;
                          setMagicScript(newScript);
                        }}
                        rows="4"
                      ></textarea>
                    </div>
                    <div style={{flex: 1}}>
                      <label style={{fontWeight: 'bold', fontSize: '0.9rem', color: '#E53935'}}>Motion Graphics (Typo & Animation):</label>
                      <textarea 
                        value={scene.graphics_prompt}
                        onChange={(e) => {
                          const newScript = [...magicScript];
                          newScript[i].graphics_prompt = e.target.value;
                          setMagicScript(newScript);
                        }}
                        rows="4"
                      ></textarea>
                    </div>
                  </div>
                  <div style={{marginTop: '10px'}}>
                    <label style={{fontWeight: 'bold', fontSize: '0.8rem', color: '#888'}}>Subtitles Höhe (Y-Pos):</label>
                    <select 
                      value={scene.y_position_override || ""}
                      onChange={(e) => {
                        const newScript = [...magicScript];
                        newScript[i].y_position_override = e.target.value ? Number(e.target.value) : null;
                        setMagicScript(newScript);
                      }}
                      style={{marginLeft: '10px', width: '150px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px'}}
                    >
                      <option value="">Standard (Global)</option>
                      <option value="15">Unten</option>
                      <option value="30">Mitte-Unten</option>
                      <option value="50">Mitte</option>
                      <option value="75">Oben</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>

            <div className="card">
               <h2>Design-Auswahl (KARAOKE-Style)</h2>
               <div className="option-row" style={{justifyContent: 'flex-start', gap: '10px', marginTop: '10px'}}>
                 <input 
                   type="checkbox" 
                   checked={!disableHyperframes} 
                   onChange={(e) => setDisableHyperframes(!e.target.checked)} 
                 />
                 <span style={{fontSize: '0.9rem', color: '#ccc'}}>Agentur-Typo-Animationen (Hyperframes) generieren</span>
               </div>
               
               <div className="option-row" style={{justifyContent: 'flex-start', gap: '10px', marginTop: '10px'}}>
                 <input 
                   type="checkbox" 
                   checked={motionGraphicsOnly} 
                   onChange={(e) => setMotionGraphicsOnly(e.target.checked)} 
                 />
                 <span style={{fontSize: '0.9rem', color: '#ccc'}}>Nur Motion Graphics (Keine KI-Bilder, pure Animation)</span>
               </div>
               
               <div className="option-row" style={{justifyContent: 'flex-start', gap: '10px', marginTop: '10px'}}>
                 <input 
                   type="checkbox" 
                   checked={!disableSubtitles} 
                   onChange={(e) => setDisableSubtitles(!e.target.checked)} 
                 />
                 <span style={{fontSize: '0.9rem', color: '#ccc'}}>Klassische Untertitel einblenden (Remotion)</span>
               </div>

               <div style={{marginTop: '20px'}}>
                 <label style={{fontWeight: 'bold', display: 'block', marginBottom: '5px', color: '#ff7b00'}}>Design- & Animations-Stil</label>
                 <select 
                   value={visualStyle} 
                   onChange={(e) => setVisualStyle(e.target.value)}
                   className="select-input"
                   style={{width: '100%', padding: '10px', background: '#222', color: 'white', border: '1px solid #444', borderRadius: '5px'}}
                 >
                   <option value="dynamic">Dynamic Mixed Media (Standard)</option>
                   <option value="tech">Tech & Futurism (Cyberpunk/HUD)</option>
                   <option value="music">Music & Entertainment (Vibrant, Bold)</option>
                   <option value="art">Art & Design (Minimalist, Elegant)</option>
                   <option value="clean">Clean & Modern (HTML5 UP Style)</option>
                 </select>
               </div>

               {options.subtitles && (
                  <>
                    <div style={{background: '#1a1a1a', padding: '20px', borderRadius: '8px', marginBottom: '20px', border: '1px solid #333'}}>
                      <h3 style={{marginTop: 0, marginBottom: '10px', color: '#fff', fontSize: '1.2rem'}}>Untertitel Sprache (Neu)</h3>
                      <p style={{fontSize: "0.9rem", color: "#666", marginBottom: "1rem"}}>Lass die KI die Untertitel automatisch übersetzen.</p>
                      <select 
                        value={subtitleLanguage} 
                        onChange={e => setSubtitleLanguage(e.target.value)}
                        style={{width: '100%', padding: '10px', background: '#222', color: 'white', border: '1px solid #444', borderRadius: '5px'}}
                      >
                        <option value="Original">Original (Keine Übersetzung)</option>
                        <option value="Englisch">Englisch</option>
                        <option value="Spanisch">Spanisch</option>
                        <option value="Französisch">Französisch</option>
                        <option value="Italienisch">Italienisch</option>
                      </select>
                    </div>
                    <StyleSelector 
                      selectedStyle={selectedStyle}
                      onStyleChange={setSelectedStyle}
                      highlightColor={highlightColor}
                      onColorChange={setHighlightColor}
                      highlightShape={highlightShape}
                      onShapeChange={setHighlightShape}
                      fontFamily={fontFamily}
                      onFontFamilyChange={setFontFamily}
                      fontWeight={fontWeight}
                      onFontWeightChange={setFontWeight}
                      textCase={textCase}
                      onTextCaseChange={setTextCase}
                      fontSize={fontSize}
                      onFontSizeChange={setFontSize}
                      yPosition={yPosition}
                      onYPositionChange={setYPosition}
                      pillRadius={pillRadius}
                      onPillRadiusChange={setPillRadius}
                      shapePadding={shapePadding}
                      onShapePaddingChange={setShapePadding}
                      popInAnimation={popInAnimation}
                      onPopInAnimationChange={setPopInAnimation}
                      keepPunctuation={keepPunctuation}
                      onKeepPunctuationChange={setKeepPunctuation}
                    />
                  </>
               )}
            </div>

            <button className="magic-button" onClick={handleRenderMagic} style={{marginTop: '20px'}}>
              ✨ Video generieren & verpacken
            </button>
            <div style={{textAlign: 'center', marginTop: '15px'}}>
               <button type="button" onClick={() => setPipelineState("new_magic")} style={{background: 'none', border: 'none', color: '#999', cursor: 'pointer', textDecoration: 'underline'}}>
                 Abbrechen & Zurück
               </button>
            </div>
          </div>
        )}

        {pipelineState === "editing" && (
          <div>
            <div style={{marginBottom: '20px'}}>
               <button onClick={() => setPipelineState("dashboard")} style={{background: '#333', color: '#fff', padding: '10px 15px', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>
                 ← Zurück zum Dashboard
               </button>
            </div>

            {options.subtitles && (
              <>
                <div style={{background: '#1a1a1a', padding: '20px', borderRadius: '8px', marginBottom: '20px', border: '1px solid #333'}}>
                  <h3 style={{marginTop: 0, marginBottom: '10px', color: '#fff', fontSize: '1.2rem'}}>Untertitel Sprache (Neu)</h3>
                  <p style={{fontSize: "0.9rem", color: "#666", marginBottom: "1rem"}}>Lass die KI die Untertitel automatisch übersetzen.</p>
                  <select 
                    value={subtitleLanguage} 
                    onChange={e => setSubtitleLanguage(e.target.value)}
                    style={{width: '100%', padding: '10px', background: '#222', color: 'white', border: '1px solid #444', borderRadius: '5px'}}
                  >
                    <option value="Original">Original (Keine Übersetzung)</option>
                    <option value="Englisch">Englisch</option>
                    <option value="Spanisch">Spanisch</option>
                    <option value="Französisch">Französisch</option>
                    <option value="Italienisch">Italienisch</option>
                  </select>
                </div>
                <StyleSelector 
                  selectedStyle={selectedStyle}
                  onStyleChange={setSelectedStyle}
                  highlightColor={highlightColor}
                  onColorChange={setHighlightColor}
                  highlightShape={highlightShape}
                  onShapeChange={setHighlightShape}
                  fontFamily={fontFamily}
                  onFontFamilyChange={setFontFamily}
                  fontWeight={fontWeight}
                  onFontWeightChange={setFontWeight}
                  textCase={textCase}
                  onTextCaseChange={setTextCase}
                  fontSize={fontSize}
                  onFontSizeChange={setFontSize}
                  yPosition={yPosition}
                  onYPositionChange={setYPosition}
                  pillRadius={pillRadius}
                  onPillRadiusChange={setPillRadius}
                  shapePadding={shapePadding}
                  onShapePaddingChange={setShapePadding}
                  popInAnimation={popInAnimation}
                  onPopInAnimationChange={setPopInAnimation}
                  keepPunctuation={keepPunctuation}
                  onKeepPunctuationChange={setKeepPunctuation}
                />
              </>
            )}
            
            {transcriptData ? (
               <TranscriptEditor 
                 transcript={transcriptData} 
                 onCancel={() => setPipelineState("dashboard")}
                 onSave={handleRenderFinal} 
               />
            ) : (
               <div className="card">
                 <p>Kein Transkript vorhanden.</p>
                 <button className="magic-button" onClick={() => handleRenderFinal({})}>
                    Video ohne Anpassungen rendern
                 </button>
               </div>
            )}
          </div>
        )}

        {pipelineState === "done" && result && (
          <div className="results-container">
            <div style={{marginBottom: '20px'}}>
               <button onClick={() => setPipelineState("dashboard")} style={{background: '#333', color: '#fff', padding: '10px 15px', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>
                 ← Zurück zum Dashboard
               </button>
            </div>

            <h2>✨ Dein VideoMagic Ergebnis ist da!</h2>
            
            <div className="result-grid">
              <EdlEditor edl={result.edl} onSave={handleRenderCustomEdl} />

              {result.video_url && (
                <div className="video-card">
                  <h3>Finales Video</h3>
                  <video controls key={result.video_url} width="100%" className="video-player">
                    <source src={result.video_url} type="video/mp4" />
                  </video>
                  <div style={{marginTop: '10px', fontSize: '0.9rem'}}>
                    <a href={result.video_url} target="_blank" rel="noreferrer" style={{color: '#3333CC', textDecoration: 'underline'}}>Video in neuem Tab öffnen</a>
                  </div>
                </div>
              )}
            </div>
            
            <div style={{marginTop: '30px', display: 'flex', gap: '15px'}}>
               <button 
                 className="magic-button" 
                 style={{flex: 1}}
                 onClick={() => {
                   setPipelineState("editing");
                 }}
               >
                 Nochmal bearbeiten (z.B. andere Untertitel-Farbe)
               </button>
               <button 
                 className="magic-button" 
                 style={{flex: 1, background: '#333'}}
                 onClick={() => {
                   setResult(null);
                   setFile(null);
                   setProjectId(null);
                   setPipelineState("dashboard");
                 }}
               >
                 Zum Dashboard
               </button>
            </div>
          </div>
        )}
      </main>
    </>
  );
}

function App() {
  const { user, loading } = useAuth();
  if (loading) return <div>Lade...</div>;
  return (
    <div className="container">
      {user ? <MainDashboard /> : <LoginScreen />}
    </div>
  );
}

export default App;
