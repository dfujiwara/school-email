# school-email

Prototype for querying Gmail through Claude Agent SDK + Gmail MCP.

## Current flow

1. Set up Google access in the browser when prompted by the MCP service.
2. Run:
   ```bash
   uv run main.py
   ```

## Notes

- `token.json` is no longer used by `main.py`.
- `auth.py` is kept only as a legacy helper for the old local OAuth flow.
- Keep `token.json` out of git if you ever create one locally.
