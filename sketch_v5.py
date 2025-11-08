# gender_aware_collage.py
# 4 SKETCHES → 1 COLLAGE | MALE/FEMALE AWARE | NO PERSON | NO COLOR
import os
import sys
import re
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# GENDER KEYWORDS
# ─────────────────────────────────────────────────────────────────────────────
MALE_KEYWORDS = {"male", "man", "men", "king", "emperor", "prince", "groom", "mens", "men's"}
FEMALE_KEYWORDS = {"female", "woman", "women", "queen", "princess", "bride", "lady", "womens", "women's"}

# ─────────────────────────────────────────────────────────────────────────────
# SAFE COLLAGE NAMING
# ─────────────────────────────────────────────────────────────────────────────
def get_next_collage_path(out_dir: Path = Path("./output")) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(r"^collage_(\d+)\.png$", re.IGNORECASE)
    max_num = 0
    for file in out_dir.iterdir():
        if file.is_file():
            match = pattern.match(file.name)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    next_num = max_num + 1
    return out_dir / f"collage_{next_num}.png"

# ─────────────────────────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────────────────────────
def build_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")
    return genai.Client(api_key=api_key)

# ─────────────────────────────────────────────────────────────────────────────
# GENDER DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def detect_gender(prompt: str) -> str:
    lowered = prompt.lower()
    if any(kw in lowered for kw in MALE_KEYWORDS):
        return "male"
    if any(kw in lowered for kw in FEMALE_KEYWORDS):
        return "female"
    return "neutral"

# ─────────────────────────────────────────────────────────────────────────────
# PROMPT LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def prepare_prompt(user_prompt: str) -> str:
    base = user_prompt.strip()
    gender = detect_gender(base)

    # Force gender-specific dress
    if gender == "male":
        base = f"{base}, male dress, menswear, tailored for man"
    elif gender == "female":
        base = f"{base}, female dress, womenswear, tailored for woman"

    # Always: no person, no color, floating
    base = (
        f"{base}, "
        "pencil sketch, black and white, no color, "
        "floating dress, no person, no model, no mannequin, "
        "isolated on pure white background, fashion illustration style"
    )
    return base

# ─────────────────────────────────────────────────────────────────────────────
# IMAGE GENERATION (FIXED)
# ─────────────────────────────────────────────────────────────────────────────
def generate_image(prompt: str) -> Image.Image | None:
    try:
        client = build_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
        )
        for part in response.parts:
            if part.inline_data:
                return Image.open(BytesIO(part.inline_data.data))
    except Exception as e:
        print(f"Error: {e}")
    return None

# ─────────────────────────────────────────────────────────────────────────────
# 2x2 COLLAGE
# ─────────────────────────────────────────────────────────────────────────────
def create_collage(images: list[Image.Image], title: str) -> Image.Image:
    if len(images) != 4:
        return None

    target_size = (500, 700)
    resized = [img.resize(target_size, Image.LANCZOS) for img in images]
    w, h = target_size
    margin = 40
    collage_w = w * 2 + margin * 3
    collage_h = h * 2 + margin * 3 + 80

    collage = Image.new("RGB", (collage_w, collage_h), "white")
    draw = ImageDraw.Draw(collage)

    # Title
    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except:
        font = ImageFont.load_default()
    title_w = draw.textlength(title, font=font)
    draw.text(((collage_w - title_w) // 2, 20), title, fill="black", font=font)

    # Paste
    positions = [
        (margin, 90),
        (w + margin * 2, 90),
        (margin, h + margin * 2 + 30),
        (w + margin * 2, h + margin * 2 + 30)
    ]
    for img, pos in zip(resized, positions):
        collage.paste(img, pos)

    # Labels
    labels = ["Var 1", "Var 2", "Var 3", "Var 4"]
    for label, pos in zip(labels, positions):
        draw.text((pos[0], pos[1] + h + 5), label, fill="gray", font=ImageFont.load_default())

    return collage

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("GENDER-AWARE FASHION COLLAGE (4-in-1)")
    print("="*55)

    raw_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("\nEnter dress prompt: ").strip()
    if not raw_prompt:
        print("No prompt – exiting.")
        return

    gender = detect_gender(raw_prompt)
    gender_label = gender.title() if gender != "neutral" else "General"
    title = f"{gender_label} Dress - 4 Variations"

    final_prompt = prepare_prompt(raw_prompt)
    print(f"Gender: {gender_label}")
    print(f"Prompt: {final_prompt!r}\n")

    print("Generating 4 sketch variations...\n")
    sketches = []

    for i in range(4):
        print(f"  → Variation {i+1}")
        img = generate_image(final_prompt)
        if img:
            sketches.append(img)
        else:
            print(f"  Failed variation {i+1}")

    if len(sketches) == 4:
        print("\nCreating collage...")
        collage = create_collage(sketches, title)
        if collage:
            filename = get_next_collage_path()
            collage.save(filename)
            print(f"\nCOLLAGE SAVED: {filename}")
        else:
            print("Failed to create collage.")
    else:
        print(f"\nOnly {len(sketches)} sketches generated.")

if __name__ == "__main__":
    main()