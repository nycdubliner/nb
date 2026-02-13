#!/usr/bin/env python3
import os
import argparse
import sys
import logging
import json
import time
from pathlib import Path

__version__ = "0.7.0"

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

def get_client(api_key=None):
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment or arguments.")
        sys.exit(1)
    try:
        return genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    except Exception as e:
        logger.error(f"Failed to initialize GenAI client: {e}")
        sys.exit(1)

def generate_images(prompt, count=1, styles=None, variations=None, aspect_ratio="2:3", output_dir="nanobanana-output", model="imagen-4.0-generate-001", api_key=None):
    client = get_client(api_key)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    enhanced_prompt = prompt
    if styles:
        enhanced_prompt += f" In styles: {', '.join(styles)}."
    if variations:
        enhanced_prompt += f" With variations: {', '.join(variations)}."

    logger.info(f"Generating {count} image(s) using model: {model}...")
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

        if response.generated_images:
            for i, generated_image in enumerate(response.generated_images):
                image_bytes = generated_image.image.image_bytes
                safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in " -_").strip()
                filename = output_path / f"{safe_prompt}_{i+1}.png"
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                logger.info(f"Saved: {filename}")
            return [str(p) for p in output_path.glob(f"{safe_prompt}_*.png")]
        else:
            logger.warning("No images were generated.")
            return []
    except Exception as e:
        logger.error(f"Error during image generation: {e}")
        sys.exit(1)

def submit_batch(prompts_file, model="gemini-2.5-flash-image", api_key=None):
    """
    Submits a batch job for a list of prompts to get the 50% discount.
    Expects a text file with one prompt per line.
    """
    client = get_client(api_key)
    prompts_path = Path(prompts_file)
    if not prompts_path.exists():
        logger.error(f"Prompts file not found: {prompts_file}")
        sys.exit(1)

    prompts = [line.strip() for line in prompts_path.read_text().splitlines() if line.strip()]
    if not prompts:
        logger.error("No prompts found in file.")
        sys.exit(1)

    # Structuring inlined requests for the Batch API
    # Note: Batch API for images usually requires GCS for large batches,
    # but some experimental endpoints support inlined requests.
    inlined_requests = [
        types.InlinedRequest(
            model=model,
            contents=[prompt],
            # Note: GenerateImagesConfig might not be directly supported in InlinedRequest 
            # for all models. If this fails, we may need to use GCS.
        ) for prompt in prompts
    ]

    logger.info(f"Submitting batch job with {len(prompts)} prompts using model {model}...")
    try:
        batch_job = client.batches.create(
            model=model,
            src=types.BatchJobSource(inlined_requests=inlined_requests)
        )
        logger.info(f"Batch job submitted successfully! ID: {batch_job.name}")
        logger.info(f"Check status with: nb batch-status {batch_job.name}")
        return batch_job.name
    except Exception as e:
        logger.error(f"Failed to submit batch job: {e}")
        sys.exit(1)

def get_batch_status(job_id, api_key=None):
    client = get_client(api_key)
    try:
        job = client.batches.get(name=job_id)
        logger.info(f"Job {job_id} status: {job.state}")
        if job.state == 'SUCCEEDED':
            logger.info("Job finished. Output location: " + str(job.output_config))
        return job.state
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="nb (NanoBanana) CLI: Google GenAI Image Generation.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    
    subparsers = parser.add_subparsers(dest="command")

    # Single Image Command
    gen_parser = subparsers.add_parser("gen", help="Generate a single image (Online)")
    gen_parser.add_argument("prompt", help="The text prompt.")
    gen_parser.add_argument("--count", type=int, default=1)
    gen_parser.add_argument("--styles", nargs="+")
    gen_parser.add_argument("--aspect_ratio", default="2:3")
    gen_parser.add_argument("--output", default="nanobanana-output")
    gen_parser.add_argument("--model", default="imagen-4.0-generate-001")
    gen_parser.add_argument("--api-key")

    # Batch Commands
    batch_parser = subparsers.add_parser("batch", help="Submit a batch job (50% Discount, Asynchronous)")
    batch_parser.add_argument("file", help="File with one prompt per line.")
    batch_parser.add_argument("--model", default="gemini-2.5-flash-image")
    batch_parser.add_argument("--api-key")

    status_parser = subparsers.add_parser("batch-status", help="Check the status of a batch job")
    status_parser.add_argument("job_id", help="The batch job name/ID.")
    status_parser.add_argument("--api-key")

    args = parser.parse_args()

    if args.command == "gen":
        generate_images(args.prompt, args.count, args.styles, None, args.aspect_ratio, args.output, args.model, args.api_key)
    elif args.command == "batch":
        submit_batch(args.file, args.model, args.api_key)
    elif args.command == "batch-status":
        get_batch_status(args.job_id, args.api_key)
    else:
        # Default to old behavior if no command but prompt exists
        # This keeps it backward compatible for the build script
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            generate_images(sys.argv[1], 1, None, None, "2:3", "nanobanana-output", "imagen-4.0-generate-001", None)
        else:
            parser.print_help()

if __name__ == "__main__":
    main()
