#!/usr/bin/env python3
import argparse
import re
import json
import shutil
import zipfile
import logging
import time
import subprocess
import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree
from .main import generate_images, submit_batch

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("comic-factory")

class ComicProject:
    def __init__(self, project_path="."):
        self.root = Path(project_path).resolve()
        self.pages_dir = self.root / "pages"
        self.assets_dir = self.root / "assets"
        self.output_dir = self.root / "renders" / "issue_01" # Defaulting for now
        
    def get_all_pages(self):
        pages = list(self.pages_dir.glob("**/p[0-9]*"))
        cover = self.pages_dir / "cover"
        if cover.exists(): pages.append(cover)
        bonus = list(self.pages_dir.glob("bonus*"))
        pages.extend(bonus)
        
        def sort_key(p):
            if p.name == "cover": return -1
            if p.name.startswith("bonus"): return 1000 + int(re.search(r'\d+', p.name).group(0) or 0)
            m = re.search(r"p(\d+)", p.name)
            return int(m.group(1)) if m else 999
        return sorted(pages, key=sort_key)

    def resolve_prompt(self, page_name, panel_num):
        # Implementation consolidated from render_page.py
        # Logic to find page_dir, manifest, and resolve tags
        pages = self.get_all_pages()
        page_dir = next((p for p in pages if p.name == page_name), None)
        if not page_dir: raise FileNotFoundError(f"Page {page_name} not found")
        
        manifest_path = page_dir / "manifest.md"
        content = manifest_path.read_text()
        
        panel_pattern = rf"### Panel {panel_num}(?:.*?)?
(.*?)(?=
### Panel|\Z)"
        match = re.search(panel_pattern, content, re.DOTALL)
        if not match: raise ValueError(f"Panel {panel_num} not found")
        
        prompt_match = re.search(r"Prompt.*?`(.*?)`", match.group(1), re.I | re.S)
        if not prompt_match: raise ValueError(f"No prompt for Panel {panel_num}")
        
        raw_prompt = prompt_match.group(1)
        resolved_prompt = raw_prompt
        tag_regex = re.compile(r"\[([^:]+):([^\]]+)\]")
        for tm in tag_regex.finditer(raw_prompt):
            tag_type = tm.group(1).lower() + "s"
            tag_value = tm.group(2)
            prompt_file = self.assets_dir / "prompts" / tag_type / f"{tag_value}.txt"
            if prompt_file.exists():
                resolved_prompt = resolved_prompt.replace(tm.group(0), prompt_file.read_text().strip().replace("
", " "))
        
        style_prefix = "Professional comic book illustration, clean ink lines, high-detail cel shading, vibrant digital colors."
        tech_append = "Portrait orientation, 2:3 aspect ratio, 6.625 x 10.25 inch comic book page layout, narrative storytelling, dramatic lighting, clear character silhouette."
        return f"{style_prefix} {resolved_prompt.strip()} {tech_append}"

def cmd_render(args):
    project = ComicProject(args.project)
    model = args.model or "nano-banana-pro-preview"
    logger.info(f"Starting Batch Render Loop using {model}...")
    
    prompts = []
    prompt_map = []
    for page_path in project.get_all_pages():
        manifest_path = page_path / "manifest.md"
        if not manifest_path.exists(): continue
        count = len(re.findall(r'### Panel', manifest_path.read_text()))
        for i in range(1, count + 1):
            prompts.append(project.resolve_prompt(page_path.name, i))
            prompt_map.append({"page": page_path.name, "panel": i, "dir": page_path})

    batch_file = project.root / "prompts_batch.txt"
    batch_file.write_text("
".join(prompts))
    
    # Use the existing submit_batch from .main
    from .main import submit_batch, get_batch_status
    job_id = submit_batch(str(batch_file), model=model)
    
    if not args.wait:
        logger.info(f"Batch submitted. ID: {job_id}. Use --wait or check status later.")
        return

    while True:
        state = get_batch_status(job_id)
        if state == 'JOB_STATE_SUCCEEDED': break
        if state in ['JOB_STATE_FAILED', 'JOB_STATE_CANCELLED']:
            logger.error(f"Job failed: {state}")
            sys.exit(1)
        time.sleep(30)
    
    # Extraction logic... (Simplified for now, would use distribute_batch_results logic)
    logger.info("Batch Succeeded. (Extraction logic to be fully integrated in factory.py)")

def main():
    parser = argparse.ArgumentParser(prog="comic-factory")
    parser.add_argument("--project", default=".", help="Path to the comic project")
    subparsers = parser.add_subparsers(dest="command")
    
    render_parser = subparsers.add_parser("render", help="Batch render all panels")
    render_parser.add_argument("--model", help="Model name")
    render_parser.add_argument("--no-wait", action="store_false", dest="wait", help="Don't wait for completion")
    render_parser.set_defaults(wait=True)
    
    # Other parsers (build, preview, etc) would go here
    
    args = parser.parse_args()
    if args.command == "render":
        cmd_render(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
