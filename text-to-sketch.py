# sketch_if_needed.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()


def build_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)


def should_force_sketch(user_prompt: str) -> bool:
    """Return True if the prompt does NOT contain the word 'sketch' (case-insensitive)."""
    return "sketch" not in user_prompt.lower()


def prepare_prompt(user_prompt: str) -> str:
    """Prepend 'pencil sketch of ' if the rule applies."""
    if should_force_sketch(user_prompt):
        return f" {user_prompt.strip()}, remember to make pencil sketch and no color, also floating dress with no person"
    return user_prompt.strip()


def next_sketch_path(out_dir: Path) -> Path:
    """
    Find the smallest integer N such that out_dir/sketch_N.png does NOT exist.
    Returns the Path for that file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    i = 1
    while True:
        candidate = out_dir / f"sketch_{i}.png"
        if not candidate.exists():
            return candidate
        i += 1


def generate_and_save(prompt: str, out_dir: Path = Path("./output")) -> None:
    client = build_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
    )

    saved = False
    for part in response.parts:
        if part.text:
            print("Text part:", part.text)
        elif part.inline_data:
            img: Image.Image = part.as_image()
            filename = next_sketch_path(out_dir)
            img.save(filename)
            print(f"Image saved to {filename.resolve()}")
            saved = True

    if not saved:
        print("No image was generated.")


def main():
    # 1. Accept prompt from CLI or interactive input
    if len(sys.argv) > 1:
        raw_prompt = " ".join(sys.argv[1:])
    else:
        raw_prompt = input("Enter your image prompt: ").strip()

    if not raw_prompt:
        print("No prompt provided – exiting.")
        return

    final_prompt = prepare_prompt(raw_prompt)
    print(f"Using prompt: {final_prompt!r}")
    generate_and_save(final_prompt)


if __name__ == "__main__":
    main()