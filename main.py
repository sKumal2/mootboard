import os
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()


def load_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found in .env file")
    return api_key

# Configure API key
client = genai.Client(api_key=load_api_key())

# Models
TEXT_MODEL_ID = "gemini-2.5-flash"
IMAGE_MODEL_ID = "gemini-2.5-flash-image"

# User prompt
user_prompt = "Create a realistic fashion moodboard featuring a model wearing the provided dress sketch, complete with suitable accessories and material swatches as it is."
sketch_path = 'image_samples/male_indian.png'
output_path = 'moodboard_output.png'

# Rephrase prompt using text model
def rephrase_prompt(prompt):
    rephrase_instruction = "Rephrase the following prompt for clarity and specificity, maintaining the original intent: " + prompt + "Do not duplicate any items. Donot add unnecessay information. Be thoughtful while generating mootboard."
    response = client.models.generate_content(
        model=TEXT_MODEL_ID,
        contents=[rephrase_instruction]
    )
    for part in response.parts:
        if part.text:
            return part.text
    return prompt  # Fallback to original if no text returned

# Save the image
def save_image(response, path):
    for part in response.parts:
        if image := part.as_image():
            image.save(path)

# Pipeline: Rephrase prompt, generate image, and save mood board
def create_moodboard(input_prompt, input_image_path, output_path):
    # Validate input image
    if not os.path.exists(input_image_path):
        raise FileNotFoundError(f"Image not found: {input_image_path}")
    
    # Rephrase prompt
    rephrased_prompt = rephrase_prompt(input_prompt)
    print(f"Rephrased prompt: {rephrased_prompt}")
    
    # Generate content with rephrased prompt
    response = client.models.generate_content(
        model=IMAGE_MODEL_ID,
        contents=[
            rephrased_prompt,
            Image.open(input_image_path)
        ]
    )
    
    # Display results
    for part in response.parts:
        if part.text:
            print(part.text)
        elif image := part.as_image():
            image.show()
    
    # Save output
    save_image(response, output_path)
    print(f"Mood board saved at: {output_path}")

# Execute pipeline
try:
    create_moodboard(user_prompt, sketch_path, output_path)
except Exception as e:
    print(f"Error: {str(e)}")