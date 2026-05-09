# school-email

Prototype for querying Gmail through Claude Agent SDK + Gmail MCP, then emailing a generated summary.

## Usage

1. Set up Google access in the browser when prompted by the MCP service.
2. Run:
   ```bash
   uv run main.py example.com recipient1@example.com recipient2@example.com
   ```
   Replace `example.com` with the sender domain you want to match, and pass one or more recipient email addresses.
3. Optional logging level:
   ```bash
   uv run main.py --log-level DEBUG example.com recipient@example.com
   ```

## What it does

- Queries emails from the past 7 days whose sender domain contains the value you pass in.
- Uses the LLM to return strict JSON shaped like `{"emails": [...]}`.
- Sorts emails in reverse chronological order, then renders the JSON into Markdown and HTML.
- Sends the HTML summary through Gmail MCP with the subject `Gmail summary for <sender_domain>`.

## Notes

- Sending happens through Gmail MCP.
- Development checks: `uv run pyright` and `uv run ruff check .`
- Keep `token.json` out of git if you ever create one locally.
