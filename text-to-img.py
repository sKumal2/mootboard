from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv
import os

load_dotenv()
def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    client = genai.Client(api_key= api_key)
    prompt = (
        "create a pencil sketch of british royal princess dress"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.as_image()
            image.save("./output/dress.png")

if __name__ == "__main__":
    main()