# AGENTS.md

## Project overview
A small Python prototype that uses Claude Agent SDK + Gmail MCP to query Gmail and send a summary email.

## Key files
- `main.py` — command-line entry point; queries Gmail for recent mail from a sender domain, formats the results, then sends the summary to one or more recipients via Gmail MCP
- `pyproject.toml` — Python/dependency metadata
- `README.md` — current usage notes

## Setup
- Python: `>=3.13`
- Dependencies are managed with `uv`

## Runtime flow
1. Run `uv run main.py <sender_domain> <recipient1> [recipient2 ...]`
2. The Gmail MCP flow prompts for Google sign-in in the browser if needed
3. `main.py` queries emails from the past 7 days whose sender email domain contains the provided domain
4. The LLM returns strict JSON, which is rendered into a plain-text email body
5. The summary is sent to the requested recipients through Gmail MCP

## Important paths / secrets
- `token.json` is sensitive; do not commit it
- Google auth happens through the MCP/browser flow; do not print secrets or credentials in logs

## Coding guidelines
- Keep changes small and focused; this repo is currently a prototype
- Prefer `pathlib.Path` for filesystem access
- Keep Gmail/MCP prompts and behavior aligned with `main.py` and the README
- If adding new scripts, document how to run them in `README.md`
- Avoid hardcoding prompts or user-specific values unless clearly intended

## Validation
- At minimum, ensure modified Python files compile:
  - `python3 -m compileall main.py`
