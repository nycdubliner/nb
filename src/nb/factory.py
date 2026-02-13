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
import yaml
import base64
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree
from .main import generate_images, submit_batch, get_batch_status

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("comic-factory")

class ComicProject:
    def __init__(self, project_path="."):
        self.root = Path(project_path).resolve()
        self.config_path = self.root / "comic.yaml"
        self.config = self._load_config()
        
        # Resolve paths from config or defaults
        paths = self.config.get("paths", {})
        self.pages_dir = self.root / paths.get("pages", "pages")
        self.assets_dir = self.root / paths.get("assets", "assets")
        self.output_dir = self.root / paths.get("output", "renders/issue_01")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.style = self.config.get("style", {})
        self.prefix = self.style.get("prefix", "Professional comic book illustration.")
        self.tech_append = self.style.get("technical", "Portrait orientation.")

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

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
        pages = self.get_all_pages()
        page_dir = next((p for p in pages if p.name == page_name), None)
        if not page_dir: raise FileNotFoundError(f"Page {page_name} not found")
        
        manifest_path = page_dir / "manifest.md"
        content = manifest_path.read_text()
        
        panel_pattern = rf"### Panel {panel_num}(?:.*?)?\n(.*?)(?=\n### Panel|\Z)"
        match = re.search(panel_pattern, content, re.DOTALL)
        if not match: raise ValueError(f"Panel {panel_num} not found")
        
        prompt_match = re.search(r"Prompt.*?\`(.*?)\`", match.group(1), re.I | re.S)
        if not prompt_match: raise ValueError(f"No prompt for Panel {panel_num}")
        
        raw_prompt = prompt_match.group(1)
        resolved_prompt = raw_prompt
        tag_regex = re.compile(r"\[([^:]+):([^\]]+)\]")
        for tm in tag_regex.finditer(raw_prompt):
            tag_type = tm.group(1).lower() + "s"
            tag_value = tm.group(2)
            prompt_file = self.assets_dir / "prompts" / tag_type / f"{tag_value}.txt"
            if prompt_file.exists():
                resolved_prompt = resolved_prompt.replace(tm.group(0), prompt_file.read_text().strip().replace("\n", " "))
        
        return f"{self.prefix} {resolved_prompt.strip()} {self.tech_append}"

    def compose(self):
        logger.info("Starting Composition (HTML Generation)...")
        for page_path in self.get_all_pages():
            manifest_path = page_path / "manifest.md"
            if not manifest_path.exists(): continue
            
            logger.info(f"  Composing {page_path.name}...")
            manifest_content = manifest_path.read_text()
            
            rows_match = re.search(r'rows: "(.*?)"', manifest_content)
            cols_match = re.search(r'cols: "(.*?)"', manifest_content)
            if not rows_match or not cols_match: continue
            
            html_content = self._generate_html_template(rows_match.group(1), cols_match.group(1))
            
            layout_matches = re.finditer(r'^\s*-\s*Panel\s+(\d+):\s*\{(.*?)\}\s*$', manifest_content, re.MULTILINE)
            for match in layout_matches:
                num, braces = match.group(1), match.group(2)
                area_match = re.search(r'grid-area: "(.*?)"', braces)
                if not area_match: continue
                lettering_html = self._parse_lettering(braces, page_path.name, num)
                
                img_path = page_path / "renders" / f"panel_{num}.png"
                html_content += f'        <div class="panel" style="grid-area: {area_match.group(1)}; background-image: url(\'file://{img_path.absolute()}\');">{lettering_html}</div>\n'

            html_content += "    </div>\n</body>\n</html>"
            (page_path / "composition.html").write_text(html_content)

    def _generate_html_template(self, rows, cols):
        return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><style>
        @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Special+Elite&display=swap');
        body {{ background-color: black; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .comic-page {{ width: 1986px; height: 3075px; background-color: black; display: grid; grid-template-rows: {rows}; grid-template-columns: {cols}; gap: 20px; padding: 40px; box-sizing: border-box; position: relative; }}
        .panel {{ background-size: cover; background-position: center; border: 8px solid black; position: relative; }}
        .caption {{ background: #ffffcc; border: 4px solid black; padding: 20px; font-family: 'Special Elite', cursive; font-size: 40px; position: absolute; max-width: 600px; box-shadow: 10px 10px 0px rgba(0,0,0,0.2); z-index: 20; }}
        .balloon-container {{ position: absolute; z-index: 30; filter: drop-shadow(5px 5px 0px rgba(0,0,0,0.3)); }}
        .balloon-text {{ background: white; border: 4px solid black; border-radius: 50%; padding: 30px 40px; font-family: 'Bangers', cursive; font-size: 45px; line-height: 1.1; text-align: center; min-width: 150px; display: inline-block; }}
        .balloon-tail {{ position: absolute; width: 50px; height: 50px; bottom: -30px; left: 50%; margin-left: -25px; background: white; border-left: 4px solid black; border-bottom: 4px solid black; transform: rotate(-45deg); z-index: -1; }}
        </style></head><body><div class="comic-page">"""

    def _parse_lettering(self, braces, page_name, num):
        lettering_match = re.search(r'lettering: \[(.*?)\]', braces)
        html = ""
        if lettering_match:
            try:
                raw_json = lettering_match.group(1).replace("type:", '"type":').replace("text:", '"text":').replace("pos:", '"pos":').replace("top:", '"top":').replace("left:", '"left":').replace("bottom:", '"bottom":').replace("right:", '"right":')
                items = json.loads(f"[{raw_json}]")
                for item in items:
                    style = "; ".join([f"{k}: {v}" for k, v in item['pos'].items()])
                    if item['type'] == 'caption':
                        html += f'<div class="caption" style="{style}">{item["text"]}</div>'
                    elif item['type'] == 'speech':
                        html += f'<div class="balloon-container" style="{style}"><div class="balloon-text">{item["text"]}</div><div class="balloon-tail"></div></div>'
            except Exception as e:
                logger.error(f"      Lettering error on P{page_name} Panel {num}: {e}")
        return html

    def rasterize(self):
        logger.info("Starting Rasterization...")
        # Standing scripts path for now
        script_path = self.root / "scripts/rasterize.py"
        if script_path.exists():
            subprocess.run([sys.executable, str(script_path)], check=True)
        else:
            logger.error("rasterize.py not found in scripts/")

    def package(self):
        logger.info("Starting Packaging (CBZ)...")
        self._generate_comic_info()
        series_name = self.config.get("series", "Comic").replace(" ", "_")
        issue_num = int(self.config.get('issue', '1'))
        cbz_name = f"{series_name}_{issue_num:02}.cbz"
        cbz_path = self.root / cbz_name
        with zipfile.ZipFile(cbz_path, 'w') as zipf:
            for img in sorted(self.output_dir.glob("*.png")):
                zipf.write(img, img.name)
            xml_path = self.output_dir / "ComicInfo.xml"
            if xml_path.exists(): zipf.write(xml_path, "ComicInfo.xml")
        logger.info(f"SUCCESS: {cbz_path} created.")

    def _generate_comic_info(self):
        root = Element("ComicInfo")
        meta = self.config.get("metadata", {})
        SubElement(root, "Series").text = self.config.get("series", "Unknown")
        SubElement(root, "Number").text = str(self.config.get("issue", "1"))
        for k, v in meta.items():
            SubElement(root, k.capitalize()).text = v
        xml_path = self.output_dir / "ComicInfo.xml"
        ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)

def cmd_init(args):
    path = Path(args.project)
    if path.exists() and any(path.iterdir()):
        logger.error(f"Directory {path} is not empty.")
        return
    
    path.mkdir(parents=True, exist_ok=True)
    (path / "pages/p01").mkdir(parents=True, exist_ok=True)
    (path / "assets/prompts/characters").mkdir(parents=True, exist_ok=True)
    (path / "assets/prompts/locations").mkdir(parents=True, exist_ok=True)
    (path / "story").mkdir(parents=True, exist_ok=True)
    
    # Create template comic.yaml
    with open(path / "comic.yaml", "w") as f:
        yaml.dump({
            "series": "My New Comic",
            "issue": 1,
            "metadata": {"writer": "Me", "penciller": "AI"},
            "style": {
                "prefix": "Professional comic book illustration.",
                "technical": "Portrait orientation, 2:3 aspect ratio."
            },
            "paths": {"pages": "pages", "assets": "assets", "output": "renders/issue_01"}
        }, f)
    
    # Create template manifest
    (path / "pages/p01/manifest.md").write_text("""# Page 01 Manifest
layout:
  rows: "1fr"
  cols: "1fr"
  panels:
    - Panel 1: { grid-area: "1 / 1 / 2 / 2", lettering: [] }

### Panel 1
- **Prompt:** `[CHARACTER:hero] standing in [LOCATION:city].`
""")
    logger.info(f"Initialized new comic project at {path}")

def cmd_render(args):
    project = ComicProject(args.project)
    model = args.model or "nano-banana-pro-preview"
    logger.info(f"Starting Batch Render Loop using {model}...")
    
    prompts, prompt_map = [], []
    for page_path in project.get_all_pages():
        manifest_path = page_path / "manifest.md"
        if not manifest_path.exists(): continue
        count = len(re.findall(r'### Panel', manifest_path.read_text()))
        for i in range(1, count + 1):
            prompts.append(project.resolve_prompt(page_path.name, i))
            prompt_map.append({"page": page_path.name, "panel": i, "dir": page_path})

    if not prompts:
        logger.warning("No prompts found.")
        return

    batch_file = project.root / "prompts_batch.txt"
    batch_file.write_text("\n".join(prompts))
    
    job_id = submit_batch(str(batch_file), model=model)
    if not args.wait:
        logger.info(f"Batch submitted. ID: {job_id}")
        return

    while True:
        state = get_batch_status(job_id)
        if state == 'JOB_STATE_SUCCEEDED': break
        if state in ['JOB_STATE_FAILED', 'JOB_STATE_CANCELLED']:
            logger.error(f"Job failed: {state}"); sys.exit(1)
        time.sleep(30)
    
    logger.info("Batch Succeeded. Distributing images...")
    distribute_batch_results(job_id, prompt_map)

def distribute_batch_results(job_id, prompt_map):
    import os
    from google import genai
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
    job = client.batches.get(name=job_id)
    
    idx = 0
    for res in job.dest.inlined_responses:
        for part in res.response.candidates[0].content.parts:
            if part.inline_data:
                if idx >= len(prompt_map): break
                mapping = prompt_map[idx]
                target_dir = Path(mapping['dir']) / "renders"
                target_dir.mkdir(parents=True, exist_ok=True)
                with open(target_dir / f"panel_{mapping['panel']}.png", "wb") as f:
                    f.write(part.inline_data.data)
                idx += 1

def main():
    parser = argparse.ArgumentParser(prog="comic-factory")
    parser.add_argument("--project", default=".", help="Path to the comic project")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("init", help="Initialize a new comic project")
    
    render_parser = subparsers.add_parser("render", help="Batch render all panels")
    render_parser.add_argument("--model")
    render_parser.add_argument("--no-wait", action="store_false", dest="wait", help="Don't wait for completion")
    render_parser.set_defaults(wait=True)
    
    subparsers.add_parser("compose", help="Generate HTML layouts")
    subparsers.add_parser("rasterize", help="Convert HTML to PNG")
    subparsers.add_parser("package", help="Create CBZ")
    
    args = parser.parse_args()
    
    if args.command == "init": cmd_init(args)
    elif args.command == "render": cmd_render(args)
    elif args.command == "compose": ComicProject(args.project).compose()
    elif args.command == "rasterize": ComicProject(args.project).rasterize()
    elif args.command == "package": ComicProject(args.project).package()
    else: parser.print_help()

if __name__ == "__main__":
    main()
