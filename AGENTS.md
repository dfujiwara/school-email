# AGENTS.md

## Project overview
A small Python prototype that uses Claude Agent SDK + Gmail MCP to query Gmail and send a generated email summary.

## Key files
- `main.py` — command-line entry point; queries Gmail for recent mail from a sender domain, renders the structured JSON response into Markdown/HTML, then sends the HTML summary to one or more recipients via Gmail MCP
- `pyproject.toml` — Python/dependency metadata
- `README.md` — current usage notes

## Setup
- Python: `>=3.13`
- Dependencies are managed with `uv`

## Runtime flow
1. Run `uv run main.py <sender_domain> <recipient1> [recipient2 ...]`
2. Optionally pass `--log-level DEBUG|INFO|WARNING|ERROR|CRITICAL`
3. The Gmail MCP flow prompts for Google sign-in in the browser if needed
4. `main.py` queries emails from the past 7 days whose sender email domain contains the provided domain
5. The LLM returns strict JSON shaped like `{"emails": [...]}`
6. The JSON is sorted in reverse chronological order, then rendered into Markdown and HTML
7. The HTML summary is sent to the requested recipients through Gmail MCP with subject `Gmail summary for <sender_domain>`

## Important paths / secrets
- `token.json` is sensitive; do not commit it
- Google auth happens through the MCP/browser flow; do not print secrets or credentials in logs

## Coding guidelines
- Keep changes small and focused; this repo is currently a prototype
- Prefer `pathlib.Path` for filesystem access
- Keep Gmail/MCP prompts and behavior aligned with `main.py` and the README
- If adding new scripts, document how to run them in `README.md`
- Avoid hardcoding prompts or user-specific values unless clearly intended
- For Python logging, use f-strings consistently

## Validation
- At minimum, ensure modified Python files compile:
  - `python3 -m compileall main.py`
- Run `uv run pyright` when changing Python logic
- Run `uv run ruff check .` when changing Python code or docs references
