import os
from dotenv import load_dotenv

import google.generativeai as genai
from PIL import Image
from io import BytesIO
from IPython.display import display, Markdown, Image as IPyImage
import PIL
import pathlib
load_dotenv()
text_prompt = "Indian Asian face on this dress, use blue color model should walk on ramp in fashion show"
image_path = 'image_samples/generated_image.png'
MODEL_ID = "gemini-2.5-flash-image"


class GeminiImageGenerator:
    def __init__(self, model_id: str):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not found in environment. Add it to your .env file.")
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(model_id)

    def display_response(self, response):
        for part in response.parts:
            if getattr(part, "text", None):
                display(Markdown(part.text))
            else:
                image = part.as_image() if hasattr(part, "as_image") else None
                if image:
                    image.show()


    def save_image(self, response, path: str):
        last_image = None
        for part in response.parts:
            image = part.as_image() if hasattr(part, "as_image") else None
            if image:
                last_image = image
        if last_image:
            last_image.save(path)

    def generate(self, prompt: str, img_path: str):
        return self.model.generate_content(
            [
                prompt,
                PIL.Image.open(img_path)
            ]
        )


generator = GeminiImageGenerator(MODEL_ID)
response = generator.generate(text_prompt, image_path)
generator.display_response(response)
generator.save_image(response, 'ropical.png')
