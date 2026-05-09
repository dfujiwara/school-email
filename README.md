# school-email

Prototype for querying Gmail through Claude Agent SDK + Gmail MCP.

## Current flow

1. Set up Google access in the browser when prompted by the MCP service.
2. Run:
   ```bash
   uv run main.py example.com recipient1@example.com recipient2@example.com
   ```
   Replace `example.com` with the sender domain you want to match, and pass one or more recipient email addresses.

## Notes

- Sending happens through Gmail MCP.
- Keep `token.json` out of git if you ever create one locally.
