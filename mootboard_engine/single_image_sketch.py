import os
import base64
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

text_prompt = "Indian Asian face on this dress, use blue color model should walk on ramp in fashion show. It shold be real human looking picture."
image_path = 'image_samples/indian_dress.png'
MODEL_ID = "gemini-2.5-flash-image"

# Convert image to base64
with open(image_path, "rb") as image_file:
    image_data = base64.b64encode(image_file.read()).decode("utf-8")

# Save the image
def save_image(response, path):
    for part in response.parts:
        if image := part.as_image():
            image.save(path)

response = client.models.generate_content(
    model=MODEL_ID,
    contents=[
        text_prompt,
        {"inline_data": {"mime_type": "image/png", "data": image_data}}
    ]
)

# Inline display
for part in response.parts:
    if part.text:
        print(part.text)
    elif image := part.as_image():
        image.show()

save_image(response, 'output_image/output.png')