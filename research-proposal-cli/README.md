```
 _    ___ __        _____      _
| |  / (_) /_  ___ / ___/_____(_)
| | / / / __ \/ _ \\__ \/ ___/ /
| |/ / / /_/ /  __/__/ / /__/ /
|___/_/_.___/\___/____/\___/_/

VibeSci - Research Proposal Generator by www.opensci.io
```

# Research Proposal CLI

Generate academic research proposals using AI.

## Prerequisites

- **Python 3.10+**
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** installed and logged in (`claude` CLI on PATH)

The CLI uses your Claude Code session (Team/Pro subscription) as its LLM backend. No API keys or credits needed.

## Quick Start

```bash
# Install
pip install -e .

# Run interactive mode
proposal generate

# Use a specific model
proposal generate --model opus

# Run with pre-filled args
proposal generate --topic "galactose oxidase mimics" --domain STEM --language English

# Convert existing markdown to PDF
proposal pdf proposal.md

# Validate an existing proposal
proposal validate proposal.md
```

## How It Works

All LLM calls go through the `claude` CLI in print mode (`claude -p`), which uses your current logged-in session. This means:

- **No API keys needed** — uses your Team/Pro subscription
- **No credit balance required** — billed through your existing plan
- **Model selection** — pass `--model sonnet`, `--model opus`, or `--model haiku`

## Pipeline

The tool runs a 6-phase workflow:

1. **Requirements** — Interactive prompts for topic, domain, language, word count
2. **Literature** — Searches arXiv, PubMed, and web for relevant papers
3. **Outline** — Generates and displays outline for user approval
4. **Writing** — Section-by-section content generation with streaming output
5. **Output** — Saves Markdown file
6. **PDF** — Optional conversion to professional PDF with cover page and TOC

## Commands

| Command | Description |
|---------|-------------|
| `proposal generate` | Full pipeline |
| `proposal generate --model opus` | Full pipeline with specific model |
| `proposal pdf <file.md>` | Standalone PDF conversion |
| `proposal validate <file.md>` | Quality checks on existing proposal |

### Generate Options

| Flag | Description |
|------|-------------|
| `--topic`, `-t` | Research topic |
| `--domain`, `-d` | STEM / Humanities / Social Sciences |
| `--language`, `-l` | English / Chinese |
| `--words`, `-w` | Target word count (default: 3000) |
| `--model`, `-m` | Claude model: sonnet (default), opus, haiku |
| `--skip-pdf` | Skip PDF conversion |

## Install Globally

### Option 1: pipx (recommended)

```bash
brew install pipx
pipx ensurepath

cd ~/Documents/research-proposal-cli
pipx install -e .

proposal generate
```

### Option 2: pip + PATH

```bash
cd ~/Documents/research-proposal-cli
pip3 install -e .

# Add the bin directory to your PATH
echo 'export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

proposal generate
```

### Option 3: Standalone binary (no Python needed)

Build a single `proposal` binary (~32 MB) that runs on any Mac without Python:

```bash
cd ~/Documents/research-proposal-cli
./build.sh

# Output: dist/proposal
# Copy to PATH:
cp dist/proposal /usr/local/bin/proposal

# Run from anywhere:
proposal generate
```

The only requirement on the target Mac is **Claude Code** (`claude` CLI installed and logged in).

### Option 4: Build & share a wheel

```bash
cd ~/Documents/research-proposal-cli
pip3 install build
python3 -m build --wheel

# Produces: dist/research_proposal_cli-0.1.0-py3-none-any.whl
# Anyone can install it:
pip3 install ./dist/research_proposal_cli-0.1.0-py3-none-any.whl
```

## Optional: Web Search

For enhanced literature search, set a web search API key:

```bash
export SERPER_API_KEY=...   # Serper.dev (free tier: 2,500 queries)
# or
export SERPAPI_KEY=...      # SerpAPI
```

Without a web search key, the tool still works — it relies on arXiv + PubMed.
