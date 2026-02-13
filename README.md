# nb (NanoBanana)

CLI tool for generating images using Google's GenAI (Imagen).

## Installation

```bash
pip install .
```

## Usage

Set your `GEMINI_API_KEY` environment variable, then:

```bash
nb "A futuristic city in the style of Moebius"
```

Options:
- `--count N`: Generate N images.
- `--styles STYLE`: Apply artistic styles.
- `--aspect_ratio RATIO`: Supported ratios: 1:1, 9:16, 16:9, 4:3, 3:4.
- `--output DIR`: Output directory.
