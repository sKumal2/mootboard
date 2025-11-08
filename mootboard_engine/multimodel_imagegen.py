# import os
# import base64
# from io import BytesIO
# from PIL import Image
# from google import genai
# from google.genai import types
# from dotenv import load_dotenv
# from pydantic import BaseModel

# IMAGE_OUPUT_PATH = "output_image/"
# class ImageClassification(BaseModel):
#     is_sketch: bool

# def load_api_key():
#     load_dotenv()
#     return os.getenv("API_KEY")

# def encode_image(image_data):
#     return base64.b64encode(image_data).decode("utf-8")

# def save_image(response, path):
#     for part in response.parts:
#         if image := part.as_image():
#             image.save(path)

# def classify_image(client, image_data):
#     prompt = "Is this a sketch or a photo of a person?"
#     response = client.models.generate_content(
#         model="gemini-2.5-flash-image",
#         contents=[prompt, {"inline_data": {"mime_type": "image/png", "data": image_data}}]
#     )
#     return ImageClassification(is_sketch="sketch" in response.parts[0].text.lower())

# def rewrite_prompt(client, original_prompt, base_image_data=None, face_image_data=None):
#     rewrite_instruction = (
#         "Rewrite this prompt to be more detailed, specific, and visually descriptive for generating a high-quality, consistent image. "
#         "Include details like lighting, background, and style to ensure a realistic and appealing output. "
#         "Do not change the design of input sketch. It should be as it is. The face should look realistic as user uploaded."
#         "Original prompt: '{}'"
#     ).format(original_prompt)
    
#     contents = [rewrite_instruction]
#     if base_image_data:
#         contents.append({"inline_data": {"mime_type": "image/png", "data": base_image_data}})
#     if face_image_data:
#         contents.append({"inline_data": {"mime_type": "image/png", "data": face_image_data}})
    
#     response = client.models.generate_content(model="gemini-2.5-flash-image", contents=contents)
#     return response.parts[0].text

# def generate_image(client, model_id, text_prompt, base_image_data, face_image_data_list=None):
#     output_paths = []
    
#     sketches = [base_image_data] if base_image_data else []
    
#     if not face_image_data_list:
#         for i, sketch in enumerate(sketches):
#             rewritten_prompt = rewrite_prompt(client, text_prompt, sketch)
#             contents = [rewritten_prompt, {"inline_data": {"mime_type": "image/png", "data": sketch}}]
#             response = client.models.generate_content(model=model_id, contents=contents)
#             path = f'output_{i}.png'
#             save_image(response, path)
#             output_paths.append(path)
#     else:
#         for i, sketch in enumerate(sketches or [None]):
#             for j, face_data in enumerate(face_image_data_list):
#                 rewritten_prompt = rewrite_prompt(client, text_prompt, sketch, face_data)
#                 contents = [rewritten_prompt]
#                 if sketch:
#                     contents.append({"inline_data": {"mime_type": "image/png", "data": sketch}})
#                 contents.append({"inline_data": {"mime_type": "image/png", "data": face_data}})
#                 response = client.models.generate_content(model=model_id, contents=contents)
#                 path = IMAGE_OUPUT_PATH + f'output_{i}_{j}.png'
#                 save_image(response, path)
#                 output_paths.append(path)
    
#     return output_paths

# def process_api_images(image_data_list, text_prompt="Design a blue dress on this body, use provided face if available, model walking on ramp"):
#     api_key = load_api_key()
#     client = genai.Client(api_key=api_key)
#     model_id = "gemini-2.5-flash-image"
    
#     sketches = []
#     faces = []
    
#     for image_data in image_data_list:
#         encoded = encode_image(image_data)
#         classification = classify_image(client, encoded)
#         if classification.is_sketch:
#             sketches.append(encoded)
#         else:
#             faces.append(encoded)
    
#     output_paths = []
    
#     if not sketches and faces:
#         output_paths.extend(generate_image(client, model_id, text_prompt, None, faces))
#     else:
#         for sketch in sketches:
#             output_paths.extend(generate_image(client, model_id, text_prompt, sketch, faces))
    
#     for path in output_paths:
#         with Image.open(path) as img:
#             img.show()
    
#     return output_paths

# def test_all_inputs():
#     test_cases = [
#         # {'name': 'single_sketch', 'files': ['image_samples/indian_dress.png']},
#         {'name': 'sketch_face', 'files': ['image_samples/indian_dress.png', 'image_samples/aish.jpg.webp']},
#         # {'name': 'sketch_multi_faces', 'files': ['image_samples/generated_image.png', 'image_samples/aish.jpg.webp', 'image_samples/face2.png']},
#         # {'name': 'multi_sketches_face', 'files': ['image_samples/generated_image.png', 'image_samples/sketch2.png', 'image_samples/aish.jpg.webp']},
#         # {'name': 'multi_sketches_faces', 'files': ['image_samples/generated_image.png', 'image_samples/sketch2.png', 'image_samples/aish.jpg.webp', 'image_samples/face2.png']},
#     ]
    
#     text_prompt = "Design a blue dress on this body, use provided face if available, model walking on ramp"
    
#     for test_case in test_cases:
#         print(f"\nRunning test: {test_case['name']}")
#         image_data_list = []
        
#         for file in test_case['files']:
#             try:
#                 with open(file, 'rb') as f:
#                     image_data_list.append(f.read())
#             except FileNotFoundError:
#                 print(f"File {file} not found, skipping...")
#                 continue
        
#         if image_data_list or test_case['name'] == 'empty':
#             output_paths = process_api_images(image_data_list, text_prompt)
#             print(f"Generated outputs: {output_paths}")
#         else:
#             print("No valid images provided for this test case.")

# if __name__ == "__main__":
#     test_all_inputs()


import os
import base64
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
import time

IMAGE_OUPUT_PATH = "output_image/"

class ImageClassification(BaseModel):
    is_sketch: bool

def load_api_key():
    load_dotenv()
    return os.getenv("GOOGLE_API_KEY")

def encode_image(image_data):
    return base64.b64encode(image_data).decode("utf-8")

def save_image(response, path):
    for part in response.parts:
        if image := part.as_image():
            image.save(path)
            return True
    return False

def classify_image(client, image_data):
    prompt = "Is this a sketch or a photo of a person? Respond with 'sketch' or 'person'."
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, {"inline_data": {"mime_type": "image/png", "data": image_data}}]
    )
    return ImageClassification(is_sketch=response.parts[0].text.lower() == "sketch")

def rewrite_prompt(client, original_prompt, base_image_data=None, face_image_data=None):
    rewrite_instruction = (
        "Rewrite this prompt to be highly detailed, specific, and visually descriptive for generating a consistent, high-quality image. "
        "Include precise details about lighting (soft, natural), background (fashion runway with elegant ambiance), "
        "model pose (confident walk), and face integration (seamless, realistic). "
        "Do not change the design of the input sketch. The model must wear the exact dress depicted in the sketch, preserving all its details, patterns, and structure. "
        "Ensure the face looks realistic as uploaded. Ensure photorealistic output with vibrant colors and sharp details. "
        "Original prompt: '{}'"
    ).format(original_prompt)
    # rewrite_instruction = (
    #     "Rewrite this prompt to be highly detailed, specific, and visually descriptive for generating a consistent, high-quality image. "
    #     "Include precise details about lighting (soft, natural), background (fashion runway with elegant ambiance), "
    #     "dress style (elegant, flowing blue fabric, modern design or classical design), model pose (confident walk), and face integration (seamless, realistic). "
    #     "Do not change the design of the input sketch. The model should always wear that sketch dress only. Ensure the face looks realistic as uploaded. "
    #     "Ensure photorealistic output with vibrant colors and sharp details. Original prompt: '{}'"
    # ).format(original_prompt)
    
    contents = [rewrite_instruction]
    if base_image_data:
        contents.append({"inline_data": {"mime_type": "image/png", "data": base_image_data}})
    if face_image_data:
        contents.append({"inline_data": {"mime_type": "image/png", "data": face_image_data}})
    
    response = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
    rewritten_prompt = response.parts[0].text
    print(f"Rewritten Prompt: {rewritten_prompt}")
    return rewritten_prompt

def generate_image(client, model_id, text_prompt, base_image_data, face_image_data_list=None, max_retries=3):
    output_paths = []
    sketches = [base_image_data] if base_image_data else []
    
    if not face_image_data_list:
        for i, sketch in enumerate(sketches):
            for attempt in range(max_retries):
                try:
                    rewritten_prompt = rewrite_prompt(client, text_prompt, sketch)
                    contents = [rewritten_prompt, {"inline_data": {"mime_type": "image/png", "data": sketch}}]
                    response = client.models.generate_content(model=model_id, contents=contents)
                    path = os.path.join(IMAGE_OUPUT_PATH, f'output_{i}.png')
                    if save_image(response, path):
                        output_paths.append(path)
                        break
                    else:
                        print(f"Attempt {attempt + 1} failed for sketch {i}. Retrying...")
                        time.sleep(1)
                except Exception as e:
                    print(f"Error in attempt {attempt + 1} for sketch {i}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
    else:
        for i, sketch in enumerate(sketches or [None]):
            for j, face_data in enumerate(face_image_data_list):
                for attempt in range(max_retries):
                    try:
                        rewritten_prompt = rewrite_prompt(client, text_prompt, sketch, face_data)
                        contents = [rewritten_prompt]
                        if sketch:
                            contents.append({"inline_data": {"mime_type": "image/png", "data": sketch}})
                        contents.append({"inline_data": {"mime_type": "image/png", "data": face_data}})
                        response = client.models.generate_content(model=model_id, contents=contents)
                        path = os.path.join(IMAGE_OUPUT_PATH, f'output_{i}_{j}.png')
                        if save_image(response, path):
                            output_paths.append(path)
                            break
                        else:
                            print(f"Attempt {attempt + 1} failed for sketch {i}, face {j}. Retrying...")
                            time.sleep(1)
                    except Exception as e:
                        print(f"Error in attempt {attempt + 1} for sketch {i}, face {j}: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(1)
    
    return output_paths

def validate_image(image_data):
    try:
        Image.open(BytesIO(image_data)).verify()
        return True
    except:
        return False

def process_api_images(image_data_list, text_prompt="Design a blue dress on this body, use provided face if available, model walking on ramp"):
    api_key = load_api_key()
    if not api_key:
        raise ValueError("API key not found in .env file")
    
    client = genai.Client(api_key=api_key)
    model_id = "gemini-2.5-flash-image"
    
    sketches = []
    faces = []
    
    for image_data in image_data_list:
        if not validate_image(image_data):
            print("Invalid image data, skipping...")
            continue
        encoded = encode_image(image_data)
        classification = classify_image(client, encoded)
        if classification.is_sketch:
            sketches.append(encoded)
        else:
            faces.append(encoded)
    
    output_paths = []
    
    if not sketches and faces:
        output_paths.extend(generate_image(client, model_id, text_prompt, None, faces))
    else:
        for sketch in sketches:
            output_paths.extend(generate_image(client, model_id, text_prompt, sketch, faces))
    
    for path in output_paths:
        with Image.open(path) as img:
            img.show()
    
    return output_paths

def test_all_inputs():
    test_cases = [
        # {'name': 'single_sketch', 'files': ['image_samples/indian_dress.png']},
        {'name': 'single_face', 'files': ['image_samples/aish.jpg.webp']},
        {'name': 'sketch_face', 'files': ['image_samples/indian_dress.png', 'image_samples/aish.jpg.webp']},
        # {'name': 'sketch_multi_faces', 'files': ['image_samples/indian_dress.png', 'image_samples/aish.jpg.webp', 'image_samples/face2.png']},
        # {'name': 'multi_sketches_face', 'files': ['image_samples/indian_dress.png', 'image_samples/sketch2.png', 'image_samples/aish.jpg.webp']},
        # {'name': 'multi_sketches_faces', 'files': ['image_samples/indian_dress.png', 'image_samples/sketch2.png', 'image_samples/aish.jpg.webp', 'image_samples/face2.png']},
        # {'name': 'empty', 'files': []}
    ]
    
    text_prompt = "Design a blue dress on this body, use provided face if available, model walking on ramp"
    
    for test_case in test_cases:
        print(f"\nRunning test: {test_case['name']}")
        image_data_list = []
        
        for file in test_case['files']:
            try:
                with open(file, 'rb') as f:
                    image_data_list.append(f.read())
            except FileNotFoundError:
                print(f"File {file} not found, skipping...")
                continue
        
        if image_data_list or test_case['name'] == 'empty':
            output_paths = process_api_images(image_data_list, text_prompt)
            print(f"Generated outputs: {output_paths}")
        else:
            print("No valid images provided for this test case.")

if __name__ == "__main__":
    os.makedirs(IMAGE_OUPUT_PATH, exist_ok=True)
    test_all_inputs()