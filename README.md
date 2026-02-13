# nb (NanoBanana) 🍌

[![CI](https://github.com/nycdubliner/nb/actions/workflows/ci.yml/badge.svg)](https://github.com/nycdubliner/nb/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**nb** is a dedicated CLI tool for Google's official GenAI Image Generation models. 

## 💰 50% Batch Discount

Save costs by using the asynchronous **Batch API**. This allows you to submit a list of prompts and get a 50% discount on supported models (e.g., \`gemini-2.5-flash-image\`).

## 🚀 Installation

\`\`\`bash
pip install .
\`\`\`

## 🛠 Usage

### ⚡ Immediate Generation (Online)
\`\`\`bash
nb gen "A neon-noir cityscape" --count 4
\`\`\`

### ⏳ Batch Generation (50% Discount)
1. Create a file \`prompts.txt\` with one prompt per line.
2. Submit the job:
   \`\`\`bash
   nb batch prompts.txt
   \`\`\`
3. Check status:
   \`\`\`bash
   nb batch-status jobs/YOUR_JOB_ID
   \`\`\`

## ⚙️ Configuration

Set your \`GEMINI_API_KEY\` as an environment variable.

## 📄 License

This project is licensed under the MIT License.
