# force_sketch_only.py
# 100% BLACK & WHITE PENCIL SKETCH — NO COLOR, NO PERSON, NO EXCEPTIONS
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TWEAKS (expanded with Roman / Royal)
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
    # NEW: ROMAN / IMPERIAL
    "roman_royal": [
        "with deep crimson silk and gold laurel leaf embroidery",
        "draped in classic toga style with purple trim",
        "featuring a golden fibula clasp and flowing pallium",
        "with intricate SPQR embroidery on the hem"
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD MAPPING (now includes Roman)
# ─────────────────────────────────────────────────────────────────────────────
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


def get_design_tweak(dress_type: str) -> str:
    if not dress_type or dress_type not in DESIGN_TWEAKS:
        return ""
    tweaks = DESIGN_TWEAKS[dress_type]
    idx = _tweak_index.get(dress_type, 0)
    tweak = tweaks[idx % len(tweaks)]
    _tweak_index[dress_type] = idx + 1
    return tweak


def clean_prompt(user_prompt: str) -> str:
    clean = user_prompt.strip()
    prefixes = ["generate ", "create ", "make ", "an image of ", "a picture of ", "image of "]
    for p in prefixes:
        if clean.lower().startswith(p.lower()):
            clean = clean[len(p):].strip()
            break
    return clean


def enhance_prompt(user_prompt: str) -> str:
    base = clean_prompt(user_prompt)
    dress_type = detect_dress_type(base)
    tweak = get_design_tweak(dress_type)
    if tweak:
        base = f"{base}, {tweak}"
    # NO PERSON, ISOLATED
    base = f"{base}, isolated on pure white background, no person, no model, no mannequin, just the garment, flat lay or hanging view"
    return base


def prepare_prompt(user_prompt: str) -> str:
    enhanced = enhance_prompt(user_prompt)
    # FORCE SKETCH — REPEATED FOR MAXIMUM OVERRIDE
    return (
        "PENCIL SKETCH ONLY. "
        "BLACK AND WHITE. "
        "NO COLOR WHATSOEVER. "
        "FASHION ILLUSTRATION STYLE. "
        "CLEAN LINES, DETAILED SHADING. "
        "NO PHOTOREALISM. "
        "MONOCHROME ONLY. "
        "NO COLOR. "
        f"{enhanced}"
    )


def get_next_filename(output_dir: Path) -> Path:
    """Find the next available filename: sketch_1.png, sketch_2.png, ..."""
    pattern = re.compile(r"^sketch_(\d+)\.png$", re.IGNORECASE)
    max_num = 0

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    for file in output_dir.iterdir():
        if file.is_file():
            match = pattern.match(file.name)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)

    next_num = max_num + 1
    return output_dir / f"sketch_{next_num}.png"


def generate_and_save(prompt: str):
    client = build_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
    )

    out_dir = Path("./output")
    filename = get_next_filename(out_dir)  # Auto-incremented name

    for part in response.parts:
        if part.inline_data:
            img = part.as_image()
            img.save(filename)
            print(f"\nSKETCH SAVED (NO COLOR): {filename.resolve()}")
            return
        if part.text:
            print("Gemini response:", part.text)
            print("No image generated.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("ROMAN-EMPIRE-READY SKETCH-ONLY FASHION DESIGNER")
    print("="*60)
    raw_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("\nEnter dress prompt: ").strip()
    if not raw_prompt:
        print("No input. Exiting.")
        return

    final_prompt = prepare_prompt(raw_prompt)
    dress_type = detect_dress_type(raw_prompt)
    style = dress_type.replace("_", " ").title() if dress_type else "General"
    print(f"\nStyle: {style}")
    print(f"Mode: BLACK & WHITE PENCIL SKETCH ONLY")
    print(f"Prompt: {final_prompt!r}\n")

    generate_and_save(final_prompt)


if __name__ == "__main__":
    main()