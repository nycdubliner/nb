#!/usr/bin/env python3
import os
import argparse
import sys
import logging
from pathlib import Path

__version__ = "0.5.0"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("nb")

try:
    from google import genai
    from google.genai import types
except ImportError:
    logger.error("Missing dependencies. Please ensure 'google-genai' is installed.")
    sys.exit(1)

def generate_images(prompt, count=1, styles=None, variations=None, aspect_ratio="2:3", output_dir="nanobanana-output", model="nanabanana-pro", api_key=None):
    """
    Core function to generate images using the specified model.
    Defaults to 'nanabanana-pro'.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment or arguments.")
        sys.exit(1)

    try:
        # Initializing client with v1alpha for experimental model support if needed
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    except Exception as e:
        logger.error(f"Failed to initialize GenAI client: {e}")
        sys.exit(1)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Combine styles and variations into the prompt if provided
    enhanced_prompt = prompt
    if styles:
        enhanced_prompt += f" In styles: {', '.join(styles)}."
    if variations:
        enhanced_prompt += f" With variations: {', '.join(variations)}."

    logger.info(f"Generating {count} image(s) using model: {model}...")
    logger.debug(f"Prompt: {enhanced_prompt}")
    logger.debug(f"Aspect Ratio: {aspect_ratio}")

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
                
                # Sanitize prompt for filename
                safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in " -_").strip()
                filename = output_path / f"{safe_prompt}_{i+1}.png"
                
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                
                logger.info(f"Saved: {filename}")
                image_count += 1
        
        if image_count == 0:
            logger.warning("No images were generated. Check your prompt or model availability.")
            return []
        
        return [str(p) for p in output_path.glob(f"{safe_prompt}_*.png")]

    except Exception as e:
        logger.error(f"Error during image generation: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="nb (NanoBanana) CLI: Google GenAI Image Generation.")
    parser.add_argument("prompt", nargs="?", help="The text prompt for image generation.")
    parser.add_argument("--count", type=int, default=1, help="Number of images to generate (1-4).")
    parser.add_argument("--styles", nargs="+", help="Artistic styles to apply.")
    parser.add_argument("--variations", nargs="+", help="Variation types to implement.")
    parser.add_argument("--aspect_ratio", default="2:3", help="Aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4).")
    parser.add_argument("--output", default="nanobanana-output", help="Output directory.")
    parser.add_argument("--model", default="nanabanana-pro", help="Google model name (default: nanabanana-pro).")
    parser.add_argument("--api-key", help="Gemini API Key.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    
    args = parser.parse_args()

    if not args.prompt:
        parser.print_help()
        sys.exit(0)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

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
