# AGENT.md

## Project overview
A small Python prototype that authenticates with Google Gmail, stores OAuth tokens locally, and uses Claude Agent SDK + Gmail MCP to query the inbox.

## Key files
- `main.py` — loads/refreshes Gmail OAuth token and queries Gmail via MCP
- `auth.py` — one-time OAuth flow that creates `token.json`
- `pyproject.toml` — Python/dependency metadata

## Setup
- Python: `>=3.13`
- Dependencies are managed with `uv`

## Runtime flow
1. Set `GOOGLE_CREDENTIALS` to a base64-encoded Google OAuth client config JSON
2. Run `auth.py` once to create `token.json`
3. Run `main.py` to query Gmail

## Important paths / secrets
- `token.json` is sensitive; do not commit it
- `GOOGLE_CREDENTIALS` contains secret OAuth client data; do not print it in logs

## Coding guidelines
- Keep changes small and focused; this repo is currently a prototype
- Prefer `pathlib.Path` for filesystem access
- Keep Gmail scopes consistent between `auth.py` and `main.py`
- If adding new scripts, document how to run them in `README.md`
- Avoid hardcoding prompts or user-specific values unless clearly intended

## Validation
- At minimum, ensure modified Python files compile:
  - `python3 -m compileall main.py auth.py`
