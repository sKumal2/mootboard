# multi_sketch_designer.py
# Generates sketch_1.png, sketch_2.png, ... with different design tweaks
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TWEAKS (expanded)
# ─────────────────────────────────────────────────────────────────────────────
DESIGN_TWEAKS = {
    "indian_bridal": [
        "with delicate zari border and subtle pearl edging",
        "featuring hand-embroidered floral butta motifs on pallu",
        "with a contrasting dupatta in soft pastel silk",
        "accented with kundan work on the blouse neckline"
    ],
    "western_gown": [
        "with an elegant asymmetric hem and soft chiffon layering",
        "featuring a deep V-neck with illusion mesh",
        "with a cinched waist and flowing train",
        "accented with subtle crystal beading along the bodice"
    ],
    "casual_day": [
        "with playful ruffled sleeves and a cinched waist bow",
        "featuring a breezy cotton fabric with polka dot print",
        "with a flared midi skirt and side pockets",
        "in soft pastel tones with a peter pan collar"
    ],
    "cultural_traditional": [
        "with authentic regional embroidery in silk thread",
        "accented with a matching silk sash and minimal floral motif",
        "featuring traditional drape and modest neckline",
        "in rich heritage colors with subtle gold piping"
    ],
    "minimalist_modern": [
        "with clean lines and a sculpted square neckline",
        "featuring geometric laser-cut patterns on sleeves",
        "in a monochrome palette with matte finish",
        "with a structured silhouette and hidden zipper"
    ],
    "bohemian": [
        "with delicate lace inserts and fringe hem detailing",
        "featuring layered earth-tone fabrics with bell sleeves",
        "accented with wooden bead trim and tassels",
        "in flowy maxi length with open back"
    ],
    "royal_princess": [
        "with a diamond-encrusted clasp and velvet cape trim",
        "featuring a crystal tiara and pearl drop earrings",
        "with hand-painted gold filigree along the hem",
        "in opulent silk with a 3-meter train"
    ],
    "roman_royal": [
        "with deep crimson silk and gold laurel leaf embroidery",
        "draped in classic toga style with purple trim",
        "featuring a golden fibula clasp and flowing pallium",
        "with intricate SPQR embroidery on the hem"
    ]
}

TYPE_KEYWORDS = {
    "indian_bridal": ["indian", "lehenga", "saree", "sari", "bridal", "wedding", "anarkali"],
    "western_gown": ["gown", "evening", "cocktail", "prom", "ballgown", "formal"],
    "casual_day": ["casual", "summer", "day", "cotton", "midi", "sundress"],
    "cultural_traditional": ["kimono", "hanbok", "ao dai", "kebaya", "cheongsam", "traditional"],
    "minimalist_modern": ["minimal", "clean", "modern", "sleek", "structured", "monochrome"],
    "bohemian": ["boho", "bohemian", "flowy", "maxi", "hippie", "fringe"],
    "royal_princess": ["royal", "princess", "cinderella", "tiara", "palace"],
    "roman_royal": ["roman", "rome", "empire", "caesar", "king", "toga", "imperial", "spqr"]
}

# Global tweak index per dress type
_tweak_index = {}

# ─────────────────────────────────────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def build_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")
    return genai.Client(api_key=api_key)

def detect_dress_type(prompt: str) -> str | None:
    lowered = prompt.lower()
    for dtype, keywords in TYPE_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return dtype
    return None

def get_next_filename() -> Path:
    out_dir = Path("./output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    existing = [f for f in out_dir.iterdir() if f.name.startswith("sketch_") and f.name.endswith(".png")]
    numbers = []
    for f in existing:
        try:
            num = int(f.stem.split("_")[1])
            numbers.append(num)
        except:
            pass
    next_num = max(numbers, default=0) + 1
    return out_dir / f"sketch_{next_num}.png"

def clean_prompt(user_prompt: str) -> str:
    clean = user_prompt.strip()
    prefixes = ["generate ", "create ", "make ", "an image of ", "a picture of ", "image of "]
    for p in prefixes:
        if clean.lower().startswith(p.lower()):
            clean = clean[len(p):].strip()
            break
    return clean

def enhance_prompt(base: str, dress_type: str) -> str:
    if not dress_type or dress_type not in DESIGN_TWEAKS:
        return base
    
    tweaks = DESIGN_TWEAKS[dress_type]
    idx = _tweak_index.get(dress_type, 0) % len(tweaks)
    tweak = tweaks[idx]
    _tweak_index[dress_type] = idx + 1
    
    enhanced = f"{base}, {tweak}"
    enhanced = f"{enhanced}, isolated on pure white background, no person, no model, no mannequin, just the garment, flat lay or hanging view"
    return enhanced

def prepare_sketch_prompt(base_prompt: str) -> str:
    dress_type = detect_dress_type(base_prompt)
    enhanced = enhance_prompt(clean_prompt(base_prompt), dress_type)
    
    return (
        "PENCIL SKETCH ONLY. "
        "BLACK AND WHITE. "
        "NO COLOR. "
        "FASHION ILLUSTRATION. "
        "CLEAN LINES, DETAILED SHADING. "
        "NO PHOTO. "
        "MONOCHROME. "
        f"{enhanced}"
    )

def generate_single_sketch(prompt: str) -> Image.Image | None:
    client = build_client()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
        )
        for part in response.parts:
            if part.inline_data:
                return part.as_image()
    except Exception as e:
        print(f"Error: {e}")
    return None

# ─────────────────────────────────────────────────────────────────────────────
# MAIN: Generate N sketches
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("MULTI-SKETCH FASHION DESIGNER (sketch_1.png, sketch_2.png, ...)")
    print("="*70)
    
    raw_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("\nEnter dress prompt: ").strip()
    if not raw_prompt:
        print("No input. Exiting.")
        return

    try:
        n_sketches = int(input("How many sketch variations? (e.g. 3): ").strip())
        if n_sketches < 1:
            n_sketches = 1
    except:
        n_sketches = 3  # default

    dress_type = detect_dress_type(raw_prompt)
    style = dress_type.replace("_", " ").title() if dress_type else "General"

    print(f"\nStyle: {style}")
    print(f"Generating {n_sketches} sketch(es)...\n")

    base_clean = clean_prompt(raw_prompt)
    for i in range(n_sketches):
        prompt = prepare_sketch_prompt(base_clean)
        print(f"Generating sketch_{i+1}...")
        img = generate_single_sketch(prompt)
        
        if img:
            filename = get_next_filename()
            img.save(filename)
            print(f"sketch_{i+1} saved → {filename}")
        else:
            print(f"Failed to generate sketch_{i+1}")

    print(f"\nAll {n_sketches} sketches saved in ./output/")

if __name__ == "__main__":
    main()