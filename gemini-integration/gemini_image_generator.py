import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Lade Umgebungsvariablen (.env aus dem Hauptverzeichnis)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def generate_image(prompt, output_filename="test_event_image.jpg"):
    """
    Generiert ein Bild mit dem gemini-3.1-flash-image-preview Modell via generateContent.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ FEHLER: GEMINI_API_KEY wurde nicht gefunden!")
        return None
    
    print(f"Generiere Bild für Prompt: '{prompt}'...")
    
    # Client initialisieren
    client = genai.Client(api_key=api_key)
    
    # API Call: Gemini 3.1 generiert Bilder über generate_content
    response = client.models.generate_content(
        model='gemini-3.1-flash-image-preview',
        contents=prompt
    )
    
    # Durchsuche die Antwort nach Bilddaten
    for part in response.candidates[0].content.parts:
        # Neuere Modelle liefern das Bild manchmal im inline_data Part
        if part.inline_data:
            with open(output_filename, "wb") as f:
                f.write(part.inline_data.data)
            print(f"✅ Bild erfolgreich generiert und gespeichert unter: {output_filename}")
            return output_filename
        elif getattr(part, 'executable_code', None) or getattr(part, 'text', None):
            continue
            
    print("❌ Kein Bild in der Antwort gefunden.")
    print("Antwort:", response.text)
    return None

if __name__ == "__main__":
    test_prompt = "A high-end cinematic shot of a futuristic event stage, glowing neon lights, strong accents of royal blue (#3333CC) and hot pink, dynamic angle, photorealistic."
    generate_image(test_prompt)
