# nb (NanoBanana) 🍌

[![CI](https://github.com/nycdubliner/nb/actions/workflows/ci.yml/badge.svg)](https://github.com/nycdubliner/nb/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**nb** is a dedicated CLI tool for Google's official GenAI Image Generation models (e.g., \`nanabanana\` and \`nanabanana-pro\`). 

It provides a streamlined interface for the [Google Gemini Image Generation API](https://ai.google.dev/gemini-api/docs/image-generation), allowing for rapid iteration on prompts, styles, and aspect ratios directly from the terminal.

## ✨ Features

- **Official Model Support:** Explicitly designed for Google's \`nanabanana\` family of models.
- **Prompt-to-Image:** Generate high-fidelity images from simple text descriptions.
- **Batch Generation:** Create multiple variations in a single command.
- **Style Presets:** Easily apply artistic styles and variations.
- **Print Ready:** Support for multiple aspect ratios (1:1, 3:4, 4:3, 16:9, 9:16).

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher.
- A Google Gemini API Key.

### From Source

1. Clone the repository:
   \`\`\`bash
   git clone https://github.com/nycdubliner/nb.git
   cd nb
   \`\`\`

2. Install the package:
   \`\`\`bash
   pip install .
   \`\`\`

## ⚙️ Configuration

Set your \`GEMINI_API_KEY\` as an environment variable:

\`\`\`bash
export GEMINI_API_KEY="your_api_key_here"
\`\`\`

Alternatively, you can provide the key directly via the \`--api-key\` flag.

## 🛠 Usage

### Basic Prompt (using default 'nanabanana')
\`\`\`bash
nb "A neon-noir cityscape in the rain"
\`\`\`

### Using the Pro model
\`\`\`bash
nb "Cybernetic forest" --model nanabanana-pro --count 4
\`\`\`

### Command Line Options

| Flag | Description | Default |
| :--- | :--- | :--- |
| \`prompt\` | The text description of the image. | (Required) |
| \`--count\` | Number of images to generate (1-4). | 1 |
| \`--aspect_ratio\` | Aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4). | 2:3 |
| \`--styles\` | Space-separated list of artistic styles. | None |
| \`--variations\` | Space-separated list of variation types. | None |
| \`--output\` | Directory to save generated images. | nanobanana-output |
| \`--model\` | The Google model name (\`nanabanana\`, \`nanabanana-pro\`). | nanabanana |
| \`--api-key\` | Explicitly provide the Gemini API key. | None |
| \`--version\` | Show the version and exit. | - |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
