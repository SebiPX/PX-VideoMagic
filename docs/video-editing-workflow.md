# Video Editing Workflow

Schritt für Schritt vom Rohvideo bis zum finalen Render.

1. **Transkription:** ElevenLabs Scribe für höchste Präzision.
2. **Cut-Planung:** Füllwörter, Pausen, Versprecher identifizieren (`pack_transcripts.py --silence-threshold 0.4`).
3. **Padding:** Exaktes Cut-Padding je nach Typ (Mid-sentence, Boundary, Video-Ende).
4. **Schnitt:** EDL erstellen und Video/Audio schneiden.
5. **Motion Graphics:** Storyboard erstellen und Hyperframes Compositions generieren.
6. **Render:** Finale Komposition über `npx hyperframes render`.
