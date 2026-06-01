# VideoMagic Studio by Pixelschickeria ✨

**VideoMagic** ist eine vollständig automatisierte, KI-gesteuerte Videoproduktions-Pipeline. Das System verknüpft rohes Videomaterial oder reine Text-Prompts mit KI-Transkription, automatischem Schnitt, Bildgenerierung, Text-To-Speech (TTS) und dynamischen Motion Graphics (Hyperframes).

## 🎯 Das Ziel
Die Kreation von hochwertigem Content für Social Media, YouTube und Event-Marketing per Knopfdruck. Ein Nutzer kann entweder ein eigenes Video hochladen und schneiden lassen ("Classic") oder ein komplett neues Video aus dem Nichts erschaffen lassen ("Magic Video").

---

## 🏗 Features & Workflows

Das Web-Dashboard (React/Vite Frontend + FastAPI Backend) bietet zwei Haupt-Workflows:

### 1. Classic Video (Automatischer KI-Schnitt)
Ideal für Talking-Head-Videos, bei denen Fehler, Ähms und lange Pausen entfernt werden sollen.
*   **Audio-Extraktion & Transkription:** Das Video wird analysiert und exakt transkribiert.
*   **KI-Schnitt (EDL):** **Gemini 2.5 Flash** analysiert das Transkript und erstellt eine JSON Edit Decision List (EDL), die Versprecher und Fehlversuche automatisch herausschneidet.
*   **Manuelle Korrektur:** Der Nutzer kann den generierten Schnittplan (EDL) im Web-UI überprüfen und per Checkboxen anpassen (Takes aktivieren/deaktivieren).
*   **Untertitel & Styling:** Zwei Untertitel-Engines (Standard "Originalsprache" und "Magic" dynamische Untertitel). Der User kann Schriftart (Google Fonts), Größe (Font Size), vertikale Position (Y-Position), Gewichtung, Groß-/Kleinschreibung (Uppercase), Highlight-Farben, Highlight-Formen (Box, Underline, Text-Color) und verschiedene Animations-Styles (Karaoke, Fade, Pop) wählen.
*   **Assets:** Optional können Intro, Outro und ein Logo-Bug (Wasserzeichen) hinzugefügt werden.

### 2. Magic Video (Text-To-Video mit Motion Graphics)
Generiert ein komplettes, professionelles Erklärvideo nur aus einem Text-Prompt.
*   **KI-Skripting:** Gemini erstellt ein mehrteiliges Video-Skript (Szenen) basierend auf dem Prompt des Users.
*   **Entwürfe (Drafts):** Die Skripte können als Entwurf gespeichert und jederzeit über das Dashboard wieder aufgerufen und editiert werden.
*   **Voice-Over:** Für jede Szene generiert **ElevenLabs** hochwertige, lebensechte KI-Stimmen (der User kann die Stimme im UI wählen).
*   **KI-Visuals:** Für den Hintergrund jeder Szene wird ein passendes Bild via **Gemini 3.1 Flash Image Preview** generiert.
*   **Dynamische Motion Graphics (Hyperframes):** 
    * Eine KI schreibt automatisiert HTML/CSS und komplexe GSAP-Animationen für den Text und die Bilder der Szene.
    * **Reviewer-KI:** Ein zweiter KI-Agent prüft den generierten Code auf Logikfehler (z.B. falsche `opacity: 0` Werte ohne Endzustand oder ungültige Viewport-Units) und korrigiert diese, um Rendering-Bugs zu verhindern.
    * Ein Headless Browser (Puppeteer) rendert die HTML-Animation Frame für Frame transparent über das Hintergrundbild.
*   **Audio-Muxing:** Die Szenen werden mit der Voice-Over-Spur, Soundeffekten und Hintergrundmusik abgemischt.
*   **Formate:** Unterstützt 9:16 (TikTok/Reels) und 16:9 (YouTube).

---

## 🛠 Architektur & Tech Stack

Das Projekt besteht aus mehreren Layern, die als Microservices zusammenarbeiten:

*   **Frontend (React/Vite):** Liegt in `web-ui/frontend`. Eine moderne Weboberfläche im Pixelschickeria-Brand-Style (Royalblau/Neon), inklusive Projekt-Dashboard.
*   **Backend (FastAPI):** Liegt in `web-ui/backend/main.py`. Der Orchestrator (Port `8001`), der die Uploads annimmt, Entwürfe verwaltet (in `projects/`) und die Pipelines steuert.
*   **Video-Engine (`video-use/helpers`):** 
    * Nutzt FFmpeg (`subprocess`) für Muxing, Cutting und Encoding.
    * Nutzt Python SDKs für Google GenAI (Gemini) und ElevenLabs.
*   **Motion Graphics Engine (`hyperframes`):** Node.js basiert, steuert Puppeteer und nutzt FFmpeg zum Extrahieren von Frames und Zusammenfügen als `.webm` mit Alphakanal.

---

## 🚀 Installation & Start

### Voraussetzungen
* Node.js & npm
* Python 3.10+
* FFmpeg (muss im PATH sein)
* `.env` Datei im `video-use` Ordner mit API Keys:
  * `GEMINI_API_KEY`
  * `ELEVENLABS_API_KEY`

### Backend starten
```bash
cd web-ui/backend
# Virtuelle Umgebung (aus video-use) nutzen
..\..\video-use\.venv\Scripts\python.exe main.py
```

### Frontend starten
```bash
cd web-ui/frontend
npm run dev
```
Das Dashboard ist dann unter `http://localhost:5173` erreichbar.

---

## 📋 Roadmap & Future Work
*   **Video-Backgrounds:** Unterstützung für generierte KI-Videos anstelle von statischen Bildern in der Magic-Pipeline (z.B. via Runway oder Sora API).
*   **Canva Integration:** Anbindung der MCP Schnittstelle, um automatisch Präsentations-Templates passend zum Video zu generieren.
*   **Live-Preview Player:** Eine integrierte Video-Vorschau im Browser, um Anpassungen am Schnitt (Classic) oder den Animationen (Magic) in Echtzeit zu sehen, bevor das endgültige Rendern gestartet wird.