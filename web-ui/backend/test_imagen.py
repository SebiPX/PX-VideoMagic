import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    print("Generating image...")
    result = client.models.generate_images(
        model='imagen-4.0-fast-generate-001',
        prompt='A futuristic sci-fi city with flying cars at night',
        config=dict(
            number_of_images=1,
            aspect_ratio="16:9",
            output_mime_type="image/jpeg",
        )
    )
    for i, generated_image in enumerate(result.generated_images):
        import base64
        with open(f"test_image_{i}.jpg", "wb") as f:
            f.write(base_image := generated_image.image.image_bytes)
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
