# nb & Comic Factory 🍌🏭

[![CI](https://github.com/nycdubliner/nb/actions/workflows/ci.yml/badge.svg)](https://github.com/nycdubliner/nb/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**nb** is a production suite for high-quality AI-generated comics. It includes a streamlined image generator (\`nb\`) and a story-agnostic production pipeline (\`comic-factory\`).

## ✨ Features

- **nb CLI:** Direct interface for Google's official GenAI Image models.
- **comic-factory:** A full-issue production engine with batch-processing support.
- **Economical Pipeline:** Automatically leverages the 50% Batch API discount.
- **Flexible Layouts:** Grid-based HTML/CSS composition with SVG lettering.

## 🚀 Installation

\`\`\`bash
git clone https://github.com/nycdubliner/nb.git
cd nb
pip install .
\`\`\`

## 🏭 Using Comic Factory

Initialize a new project:
\`\`\`bash
mkdir my-comic && cd my-comic
comic-factory init
\`\`\`

Run the production loop:
1. \`comic-factory render\` (Parallel Batch Generation)
2. \`comic-factory compose\` (HTML Composition)
3. \`comic-factory rasterize\` (Headless Rasterization)
4. \`comic-factory package\` (CBZ Packaging)

## 📄 License

This project is licensed under the MIT License.
