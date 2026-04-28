# devwatch 🛠️

> All-in-one developer utility CLI — monitor · summarize · organize · chat

A Python CLI tool that bundles four useful developer tools into one clean command. Built for Ubuntu/Linux.

---

## Features

| Command | What it does |
|---|---|
| `monitor` | Check if URLs/APIs are up and measure response time |
| `summarize` | Fetch any webpage and get an AI-powered summary |
| `organize` | Auto-sort a messy folder into subfolders by file type |
| `chat` | Chat with Claude AI right in your terminal |

---

## Install

```bash
git clone https://github.com/yourname/devwatch.git
cd devwatch
pip install -e . --break-system-packages
```

## Setup (for AI features)

```bash
export ANTHROPIC_API_KEY=your_key_here
# or persist it:
devwatch config --key your_key_here
```

## Usage

### Monitor URLs
```bash
devwatch monitor https://google.com https://github.com
devwatch monitor --add https://mysite.com
devwatch monitor --watch 10 --interval 30
```

### Summarize a Webpage
```bash
devwatch summarize https://news.ycombinator.com
devwatch summarize https://some-article.com --length short --save out.txt
```

### Organize Files
```bash
devwatch organize ~/Downloads --dry-run
devwatch organize ~/Downloads -y
```

### Chat with AI
```bash
devwatch chat
```

### Config
```bash
devwatch config --key sk-ant-...
devwatch config --show
```

## Tech Stack
- Python 3.8+ (zero external dependencies)
- Anthropic Claude API for AI features
- Ubuntu / Linux

## License
MIT
