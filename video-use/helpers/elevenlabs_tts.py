import os
import requests
import sys

def get_voices():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return []
        
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("voices", [])
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return []

def generate_speech(text: str, voice_id: str, output_path: str):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not found in environment")
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    
    return output_path

if __name__ == "__main__":
    # Test script
    from dotenv import load_dotenv
    load_dotenv()
    if len(sys.argv) > 2:
        generate_speech(sys.argv[1], sys.argv[2], "test_tts.mp3")
        print("Generated test_tts.mp3")
    else:
        print(get_voices()[:2])
