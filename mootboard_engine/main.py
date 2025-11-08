import os
import base64
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
import time
from typing import List, Optional
import mimetypes

IMAGE_OUTPUT_PATH = "output_image/"

class ImageClassification(BaseModel):
    is_sketch: bool

def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found in .env file")
    return api_key

def get_mime_type(image_data: bytes) -> str:
    """Detect MIME type from image data."""
    try:
        img = Image.open(BytesIO(image_data))
        format_to_mime = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'JPG': 'image/jpeg',
            'WEBP': 'image/webp',
            'GIF': 'image/gif'
        }
        return format_to_mime.get(img.format, 'image/png')
    except:
        return 'image/png'

def encode_image(image_data: bytes) -> str:
    return base64.b64encode(image_data).decode("utf-8")

def validate_image(image_data: bytes) -> bool:
    """Validate image data before processing."""
    try:
        img = Image.open(BytesIO(image_data))
        img.verify()
        return True
    except Exception as e:
        print(f"Image validation failed: {e}")
        return False

def classify_image(client, image_data: str, mime_type: str) -> bool:
    """Classify if image is a sketch or photo using Gemini 2.5 Flash. Returns True if sketch."""
    try:
        prompt = """Analyze this image and determine:
Is this a SKETCH/DRAWING/ILLUSTRATION (hand-drawn, digital art, line art, fashion sketch)
OR a PHOTOGRAPH/REAL PHOTO of a person?

Respond with ONE word: 'sketch' or 'photo'

Indicators:
- Sketch: Artistic lines, fashion design, no realistic skin texture
- Photo: Realistic skin, hair, camera-captured"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, {"inline_data": {"mime_type": mime_type, "data": image_data}}]
        )
        result = response.parts[0].text.strip().lower()
        is_sketch = "sketch" in result
        print(f"  Classification result: {result} -> {'SKETCH' if is_sketch else 'PHOTO'}")
        return is_sketch
    except Exception as e:
        print(f"Classification error: {e}")
        return False

def extract_face_description(client, face_data: tuple) -> str:
    """Extract detailed face description from reference image using Gemini 2.5 Flash."""
    encoded, mime = face_data
    prompt = (
        "Describe this person's face in detail for image generation: "
        "facial structure, skin tone, eye shape and color, nose shape, "
        "lip shape, face shape, hair style and color, distinctive features. "
        "Start with 'A person with...'"
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, {"inline_data": {"mime_type": mime, "data": encoded}}]
        )
        description = response.parts[0].text.strip()
        print(f"Face description: {description}")
        return description
    except Exception as e:
        print(f"Error extracting face description: {e}")
        return ""

def create_enhanced_prompt(base_prompt: str, has_sketch: bool, has_face: bool, face_description: str = "") -> str:
    """Create an enhanced prompt to reduce hallucination."""
    if has_sketch and has_face:
        return (
            f"{base_prompt}\n\n"
            f"{face_description}\n\n"
            "Use exact dress design from sketch. Photorealistic fashion photo, not cartoon/illustration. "
            "Professional lighting, runway setting."
        )
    elif has_sketch:
        return (
            f"{base_prompt}\n\n"
            "Use exact dress design from sketch. "
            "PHOTOREALISTIC fashion model (real human with realistic skin and features, NOT cartoon/illustration/anime). "
            "Professional fashion photography, runway setting."
        )
    elif has_face:
        return (
            f"{base_prompt}\n\n"
            "CRITICAL: Use the EXACT face from the reference photo - same person, same features. "
            "Photorealistic fashion image, professional quality."
        )
    return base_prompt

def generate_single_image(
    client,
    model_id: str,
    prompt: str,
    sketch_data: Optional[tuple] = None,
    face_data: Optional[tuple] = None,
    output_name: str = "output",
    max_retries: int = 3
) -> Optional[str]:
    """Generate a single image with retry logic using Imagen 4.0."""
    has_sketch = sketch_data is not None
    has_face = face_data is not None
    face_description = extract_face_description(client, face_data) if has_face else ""
    
    enhanced_prompt = create_enhanced_prompt(prompt, has_sketch, has_face, face_description)
    
    print(f"\n{'='*60}")
    print(f"Generating: {output_name}")
    print(f"Has sketch: {has_sketch}, Has face: {has_face}")
    print(f"\nPrompt:\n{enhanced_prompt}")
    print(f"{'='*60}")
    
    # Prepare image data for API
    inline_data = []
    if sketch_data:
        encoded, mime = sketch_data
        inline_data.append({"inline_data": {"mime_type": mime, "data": encoded}})
        print(f"Added sketch ({mime})")
    if face_data:
        encoded, mime = face_data
        inline_data.append({"inline_data": {"mime_type": mime, "data": encoded}})
        print(f"Added face reference ({mime})")
    
    output_path = os.path.join(IMAGE_OUTPUT_PATH, f'{output_name}.png')
    
    for attempt in range(max_retries):
        try:
            print(f"Generation attempt {attempt + 1}/{max_retries}...")
            # Pass prompt as string, handle inline data separately if API supports
            response = client.models.generate_images(
                model=model_id,
                prompt=enhanced_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    # Note: Inline data handling depends on API; adjust if needed
                    additional_data=inline_data if inline_data else None
                )
            )
            for generated_image in response.generated_images:
                generated_image.image.save(output_path)
                print(f"Image saved: {output_path}")
                return output_path
            print(f"Attempt {attempt + 1} failed - no image in response")
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
        if attempt < max_retries - 1:
            time.sleep(2)
    
    print(f"Failed to generate {output_name} after {max_retries} attempts")
    return None

def process_images(
    image_data_list: List[tuple],
    text_prompt: str,
    model_id: str = "imagen-4.0-generate-001"
) -> List[str]:
    """Main processing function."""
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    
    sketches = []
    faces = []
    
    print("\n" + "="*60)
    print("CLASSIFYING IMAGES")
    print("="*60)
    
    for idx, (image_data, mime_type) in enumerate(image_data_list):
        print(f"\nImage {idx} ({mime_type}):")
        if not validate_image(image_data):
            print(f" Invalid image data, skipping")
            continue
        encoded = encode_image(image_data)
        is_sketch = classify_image(client, encoded, mime_type)
        if is_sketch:
            sketches.append((encoded, mime_type))
            print(f"  ✓ Added to SKETCHES")
        else:
            faces.append((encoded, mime_type))
            print(f"  ✓ Added to FACES")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(sketches)} sketch(es), {len(faces)} face(s)")
    print(f"{'='*60}")
    
    output_paths = []
    if not sketches and not faces:
        print("No valid images to process")
        return output_paths
    
    print("\n" + "="*60)
    print("GENERATING IMAGES")
    print("="*60)
    
    if faces and not sketches:
        print("\nMode: FACE ONLY (creating outfit from prompt)")
        for i, face in enumerate(faces):
            path = generate_single_image(
                client, model_id, text_prompt,
                sketch_data=None, face_data=face, output_name=f"face_only_{i}"
            )
            if path:
                output_paths.append(path)
    
    elif sketches and not faces:
        print("\nMode: SKETCH ONLY (creating photorealistic moodboard)")
        for i, sketch in enumerate(sketches):
            path = generate_single_image(
                client, model_id, text_prompt,
                sketch_data=sketch, face_data=None, output_name=f"sketch_only_{i}"
            )
            if path:
                output_paths.append(path)
    
    else:
        print("\nMode: SKETCH + FACE (applying face to dress design)")
        for i, sketch in enumerate(sketches):
            for j, face in enumerate(faces):
                path = generate_single_image(
                    client, model_id, text_prompt,
                    sketch_data=sketch, face_data=face, output_name=f"sketch_{i}_face_{j}"
                )
                if path:
                    output_paths.append(path)
    
    return output_paths

def display_images(image_paths: List[str]):
    """Display generated images."""
    for path in image_paths:
        try:
            with Image.open(path) as img:
                img.show()
        except Exception as e:
            print(f"Error displaying {path}: {e}")

def main():
    """Main execution function."""
    os.makedirs(IMAGE_OUTPUT_PATH, exist_ok=True)
    
    text_prompt = "Design a blue color dress on model using the given sketch, use provided face if available, model walking on ramp"
    
    # Placeholder for image inputs (replace with actual file paths or uploaded images)

    test_files = [
            'image_samples/indian_dress.png',  # Example sketch
            'image_samples/aishs.jpg'          # Example face
        ]
    
    image_data_list = []
    print("\n" + "="*60)
    print("LOADING IMAGES")
    print("="*60)
    
    for file_path in test_files:
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
                mime_type = get_mime_type(image_data)
                image_data_list.append((image_data, mime_type))
                print(f"✓ Loaded: {file_path} ({mime_type})")
        except FileNotFoundError:
            print(f"File not found: {file_path}")
    
    if not image_data_list:
        print("\nNo valid images to process")
        # Simulate face image since you mentioned a webp face reference
        image_data_list = [(b"placeholder_face_data", "image/webp")]
    
    output_paths = process_images(image_data_list, text_prompt)
    
    print(f"\n{'='*60}")
    print(f"✓ GENERATION COMPLETE!")
    print(f"{'='*60}")
    print(f"Created {len(output_paths)} image(s):")
    for path in output_paths:
        print(f"  • {path}")
    print(f"{'='*60}\n")
    
    if output_paths:
        display_images(output_paths)

if __name__ == "__main__":
    main()