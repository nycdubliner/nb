#!/usr/bin/env python3
import os
import argparse
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: Missing dependencies. Please ensure google-genai is installed.")
    sys.exit(1)

def generate_images(prompt, count=1, styles=None, variations=None, aspect_ratio="2:3", output_dir="nanobanana-output", model="imagen-4.0-generate-001", api_key=None):
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment or arguments.")
        sys.exit(1)

    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Combine styles and variations into the prompt if provided
    enhanced_prompt = prompt
    if styles:
        enhanced_prompt += f" In styles: {', '.join(styles)}."
    if variations:
        enhanced_prompt += f" With variations: {', '.join(variations)}."

    print(f"Generating {count} image(s) with model {model}...")
    print(f"Prompt: {enhanced_prompt}")
    print(f"Aspect Ratio: {aspect_ratio}")

    try:
        response = client.models.generate_images(
            model=model,
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=count,
                aspect_ratio=aspect_ratio,
                output_mime_type='image/png'
            )
        )

        image_count = 0
        if response.generated_images:
            for i, generated_image in enumerate(response.generated_images):
                image_bytes = generated_image.image.image_bytes
                
                safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in " -_").strip()
                filename = output_path / f"{safe_prompt}_{i+1}.png"
                
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                
                print(f"Saved: {filename}")
                image_count += 1
        
        if image_count == 0:
            print("No images were generated.")
            return []
        
        return [str(p) for p in output_path.glob(f"{safe_prompt}_*.png")]

    except Exception as e:
        print(f"Error during generation: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="NanoBanana CLI (nb) for image generation.")
    parser.add_argument("prompt", help="The text prompt for image generation.")
    parser.add_argument("--count", type=int, default=1, help="Number of images to generate (default: 1).")
    parser.add_argument("--styles", nargs="+", help="Artistic styles to apply.")
    parser.add_argument("--variations", nargs="+", help="Variation types to implement.")
    parser.add_argument("--aspect_ratio", default="2:3", help="Aspect ratio (default: 2:3).")
    parser.add_argument("--output", default="nanobanana-output", help="Output directory for generated images.")
    parser.add_argument("--model", default="imagen-4.0-generate-001", help="The model to use (default: imagen-4.0-generate-001).")
    parser.add_argument("--api-key", help="Gemini API Key (optional, defaults to GEMINI_API_KEY env var).")
    
    args = parser.parse_args()
    generate_images(
        args.prompt, 
        count=args.count, 
        styles=args.styles, 
        variations=args.variations, 
        aspect_ratio=args.aspect_ratio, 
        output_dir=args.output, 
        model=args.model,
        api_key=args.api_key
    )

if __name__ == "__main__":
    main()
