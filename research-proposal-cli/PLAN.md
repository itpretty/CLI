# Plan: Convert `research-proposal` Skill to a Python CLI

## Context

The `research-proposal` skill is currently a Claude Code skill (`SKILL.md` + reference files) that generates PhD research proposals through a 6-phase workflow. It relies on Claude Code's agentic loop for LLM generation, web search, Zotero MCP, and interactive user approval. The goal is to convert this into a **standalone Python CLI** that can run independently of Claude Code.

### Decisions Made
- **LLM Provider**: Anthropic Claude (Python SDK)
- **Interactivity**: Interactive mode (step-by-step prompts)
- **Zotero**: Deferred to later phase — start with web search + arXiv/PubMed only
- **Location**: `~/Documents/research-proposal-cli` (separate repo)

---

## Phase 1: Project Scaffolding

### 1.1 Directory Structure

```
~/Documents/research-proposal-cli/
├── pyproject.toml                  # Project metadata, dependencies, entry point
├── README.md                       # Usage docs
├── .env.example                    # Template for API keys
├── src/
│   └── proposal/
│       ├── __init__.py
│       ├── cli.py                  # Entry point — typer/click CLI
│       ├── config.py               # Settings, API key loading, defaults
│       ├── phases/
│       │   ├── __init__.py
│       │   ├── requirements.py     # Phase 1: interactive requirements gathering
│       │   ├── literature.py       # Phase 2: literature search & organization
│       │   ├── outline.py          # Phase 3: outline generation + user approval
│       │   ├── writing.py          # Phase 4: content generation
│       │   ├── output.py           # Phase 5: markdown file output
│       │   └── pdf.py              # Phase 6: PDF conversion (wraps existing script)
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── client.py           # Anthropic SDK wrapper, retry logic, token tracking
│       │   └── prompts.py          # System prompts assembled from reference files
│       ├── search/
│       │   ├── __init__.py
│       │   ├── web.py              # Web search (SerpAPI or Serper)
│       │   ├── arxiv_search.py     # arxiv Python package wrapper
│       │   └── pubmed.py           # PubMed/Entrez API wrapper
│       └── validators/
│           ├── __init__.py
│           └── quality.py          # Automated quality checks (word count, ref count, etc.)
├── templates/                      # Copied from skill
│   ├── proposal_scaffold_en.md
│   ├── proposal_scaffold_zh.md
│   ├── STRUCTURE_GUIDE.md
│   ├── DOMAIN_TEMPLATES.md
│   ├── WRITING_STYLE_GUIDE.md
│   ├── QUALITY_CHECKLIST.md
│   └── LITERATURE_WORKFLOW.md
├── fonts/                          # Copied from skill
│   ├── STIXTwoText-Regular.ttf
│   ├── STIXTwoText-Bold.ttf
│   ├── STIXTwoText-Italic.ttf
│   ├── STIXTwoText-BoldItalic.ttf
│   └── STIXTwoMath-Regular.ttf
└── scripts/
    └── md_to_pdf.py                # Copied from skill (adapted import paths)
```

### 1.2 Dependencies

```
anthropic              # LLM API
typer[all]             # CLI framework (includes rich, shellingham)
rich                   # Terminal formatting, progress bars, panels
questionary            # Interactive prompts (outline approval, etc.)
python-dotenv          # .env loading for API keys
reportlab              # PDF generation (existing md_to_pdf.py)
arxiv                  # arXiv API
pymed                  # PubMed API (or biopython)
httpx                  # HTTP client for web search APIs
pydantic               # Data models for config, literature entries, proposal sections
```

### 1.3 Files to Copy from Existing Skill

Source: `/Users/ritingliu/Documents/mini-research/.claude/skills/research-proposal/`

| Source | Destination | Modifications |
|--------|-------------|---------------|
| `assets/proposal_scaffold_en.md` | `templates/proposal_scaffold_en.md` | None |
| `assets/proposal_scaffold_zh.md` | `templates/proposal_scaffold_zh.md` | None |
| `references/STRUCTURE_GUIDE.md` | `templates/STRUCTURE_GUIDE.md` | None |
| `references/DOMAIN_TEMPLATES.md` | `templates/DOMAIN_TEMPLATES.md` | None |
| `references/WRITING_STYLE_GUIDE.md` | `templates/WRITING_STYLE_GUIDE.md` | None |
| `references/QUALITY_CHECKLIST.md` | `templates/QUALITY_CHECKLIST.md` | None |
| `references/LITERATURE_WORKFLOW.md` | `templates/LITERATURE_WORKFLOW.md` | None |
| `scripts/md_to_pdf.py` | `scripts/md_to_pdf.py` | Update font path resolution |
| `scripts/fonts/*` | `fonts/*` | None |

---

## Phase 2: Core Modules (Build Order)

### Step 1: `config.py` — Settings & API Key Management

- Load `ANTHROPIC_API_KEY` from env / `.env` file
- Load optional `SERPAPI_KEY` or `SERPER_API_KEY` for web search
- Define defaults: model name (`claude-sonnet-4-20250514`), word count (3000), language (English), domain (STEM)
- Use `pydantic.BaseSettings` for validation

### Step 2: `llm/client.py` — Anthropic SDK Wrapper

- Thin wrapper around `anthropic.Anthropic().messages.create()`
- Handles: retry on rate limits, token usage tracking, streaming output to terminal
- Key method: `generate(system_prompt: str, user_prompt: str, max_tokens: int) -> str`
- Token budget tracking: log input/output tokens per call, cumulative total

### Step 3: `llm/prompts.py` — System Prompt Assembly

- Read template files from `templates/` directory at runtime
- Assemble system prompts for each phase:
  - **Outline prompt**: STRUCTURE_GUIDE + DOMAIN_TEMPLATES + user requirements → outline
  - **Writing prompt**: WRITING_STYLE_GUIDE + QUALITY_CHECKLIST + approved outline + literature summaries → full proposal
- Manage context window budget: prioritize which reference files to include based on available tokens
- Template variable substitution: `{topic}`, `{domain}`, `{language}`, `{word_count}`

### Step 4: `search/web.py` — Web Search

- Support SerpAPI or Serper.dev (both have free tiers)
- Method: `search(query: str, num_results: int = 10) -> list[SearchResult]`
- `SearchResult` dataclass: title, url, snippet, date
- Rate limiting: simple sleep between requests

### Step 5: `search/arxiv_search.py` — arXiv Search

- Use `arxiv` Python package
- Method: `search(query: str, max_results: int = 10) -> list[Paper]`
- `Paper` dataclass: title, authors, abstract, year, arxiv_id, url

### Step 6: `search/pubmed.py` — PubMed Search

- Use `pymed` or direct Entrez API via `httpx`
- Method: `search(query: str, max_results: int = 10) -> list[Paper]`
- Same `Paper` dataclass as arXiv

---

## Phase 3: Pipeline Phases (Build Order)

### Step 7: `phases/requirements.py` — Interactive Requirements Gathering

- Use `questionary` for interactive prompts:
  1. Research topic/direction (free text)
  2. Academic domain (choice: STEM / Humanities / Social Sciences)
  3. Output language (choice: English / Chinese)
  4. Target word count (default 3000, numeric input)
  5. Target institution (optional free text)
- Return a `ProposalRequirements` pydantic model
- Display summary with `rich.panel` for user confirmation

### Step 8: `phases/literature.py` — Literature Collection

- Orchestrate searches across web + arXiv + PubMed based on domain:
  - STEM: arXiv + PubMed + web
  - Humanities: web only (arXiv/PubMed not relevant)
  - Social Sciences: PubMed + web
- Generate search queries from topic (3-5 variants: reviews, methodology, gaps, trends)
- Collect and deduplicate results
- Use LLM to **summarize and categorize** results into 5 categories:
  1. Background/Context
  2. State-of-the-Art
  3. Gap-Identifying
  4. Methodology
  5. Related Work
- Display progress with `rich.progress` bar
- Return structured `LiteratureCollection` model

### Step 9: `phases/outline.py` — Outline Generation + Approval

- Assemble prompt from: requirements + literature summaries + STRUCTURE_GUIDE + DOMAIN_TEMPLATES
- Single LLM call → structured outline (Markdown)
- Display outline in terminal with `rich.markdown`
- Interactive approval loop:
  - "Approve" → proceed
  - "Edit" → user provides modification instructions → re-generate
  - "Reject" → start over or exit
- Return approved `ProposalOutline` model

### Step 10: `phases/writing.py` — Content Generation

- **Key challenge**: generating ~3,000 words + 40 references in a single coherent document
- Strategy: **section-by-section generation** with shared context
  1. Generate Abstract (after all other sections, or as a summary pass)
  2. Generate Introduction (with literature context)
  3. Generate Literature Review (heaviest literature dependency)
  4. Generate Methodology
  5. Generate Timeline
  6. Generate Significance
  7. Generate References list
  8. Final pass: generate Abstract summarizing all sections
- Each section call includes:
  - System prompt: WRITING_STYLE_GUIDE excerpt relevant to that section
  - User prompt: approved outline for that section + literature summaries + previously generated sections (for coherence)
- Stream output to terminal as it generates (section by section)
- Return complete Markdown string

### Step 11: `phases/output.py` — File Output

- Write Markdown to `proposal_{topic_slug}_{date}.md`
- Prompt user for output directory (default: current directory)
- Display file path with `rich.console`

### Step 12: `phases/pdf.py` — PDF Conversion

- Wrap existing `md_to_pdf.py` as a function call (it already has `build_pdf()`)
- Adjust font path resolution to use the CLI's `fonts/` directory
- Ask user: "Convert to PDF?" (yes/no)
- If yes, call `build_pdf(md_path, pdf_path)`

---

## Phase 4: CLI Entry Point

### Step 13: `cli.py` — Main CLI

- Use `typer` for the CLI framework
- Main command: `proposal generate`
  - Runs the full 6-phase pipeline sequentially
  - Options: `--topic`, `--domain`, `--language`, `--words` (skip interactive prompts if provided)
  - Flag: `--skip-pdf` to skip PDF conversion
- Utility commands:
  - `proposal pdf <input.md>` — standalone PDF conversion
  - `proposal validate <input.md>` — run quality checks on existing proposal
- Display a welcome banner and phase progress indicator with `rich`

---

## Phase 5: Validators

### Step 14: `validators/quality.py` — Automated Quality Checks

Automated checks that don't require LLM:
- Total word count (target ±10%)
- Per-section word count ranges (from STRUCTURE_GUIDE)
- Reference count (minimum 40)
- Reference recency (60% from last 5 years — parse years from reference text)
- Abbreviation first-use check (regex for uppercase abbreviations, verify they appear in parentheses on first mention)
- Heading structure validation (required sections present)
- Citation format consistency (APA parenthetical pattern)
- Figure suggestion count (3-5)

Display results as a checklist with `rich.table` (pass/fail per item).

---

## Phase 6: Testing & Verification

### How to Verify End-to-End

1. **Unit tests**: Each search module returns expected dataclass shapes with mocked API responses
2. **Integration test**: Run full pipeline with a test topic, verify output Markdown has all required sections, ≥40 references, correct word count range
3. **PDF test**: Convert a sample Markdown proposal to PDF, verify it opens and has cover + TOC + content pages
4. **Manual smoke test**: Run `proposal generate` interactively with a real topic, review the output quality

### Test Command
```bash
cd ~/Documents/research-proposal-cli
# Install in dev mode
pip install -e ".[dev]"
# Run
proposal generate
# Or with pre-filled args
proposal generate --topic "galactose oxidase mimics" --domain STEM --language English
```

---

## Implementation Order Summary

| Step | Module | Effort | Depends On |
|------|--------|--------|------------|
| 1 | Project scaffold + copy templates/fonts | Small | — |
| 2 | `config.py` | Small | — |
| 3 | `llm/client.py` | Small | config |
| 4 | `llm/prompts.py` | Medium | templates |
| 5 | `search/web.py` | Small | config |
| 6 | `search/arxiv_search.py` | Small | — |
| 7 | `search/pubmed.py` | Small | — |
| 8 | `phases/requirements.py` | Small | config |
| 9 | `phases/literature.py` | Medium | search/*, llm |
| 10 | `phases/outline.py` | Medium | llm, requirements |
| 11 | `phases/writing.py` | **Large** | llm, outline, literature |
| 12 | `phases/output.py` | Small | writing |
| 13 | `phases/pdf.py` | Small | existing script |
| 14 | `cli.py` | Medium | all phases |
| 15 | `validators/quality.py` | Medium | — |

**Estimated total**: ~2,000-2,500 lines of Python (excluding copied files)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM token costs add up (40+ refs = large context) | Track tokens per call, warn user of estimated cost before proceeding |
| Section-by-section writing may lose coherence | Pass previous sections as context; final "coherence pass" with LLM |
| Web search API requires paid key | Support multiple providers; gracefully degrade to arXiv/PubMed-only if no key |
| Generated references may be hallucinated | Post-generation validator flags suspicious entries; user warned to verify |
| Context window overflow on large proposals | Budget tokens per section; truncate literature summaries if needed |

---

## Future Enhancements (Not in V1)

- Zotero integration via `pyzotero`
- `--non-interactive` batch mode with YAML config files
- OpenAI/other LLM provider support
- Web UI (Streamlit/Gradio) frontend
- Reference verification against CrossRef/Semantic Scholar APIs
- Multi-language support beyond EN/ZH
