# school-email

Prototype for summarizing Gmail with Claude skills plus Google Workspace CLI, then emailing a generated summary.

## Usage

1. If you run the Python prototype, complete Google sign-in in the browser when prompted.
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

- Uses Claude with the local skill and `gws` via bash to query emails from the past 7 days whose sender domain contains the value you pass in.
- Uses the LLM to return strict JSON shaped like `{"emails": [...]}`.
- Sorts emails in reverse chronological order, then renders the JSON into Markdown and HTML.
- Sends the HTML summary with the subject `Gmail summary for <sender_domain>`.

## Notes

- The repo includes a local Claude skill at `.claude/skills/school-email/SKILL.md`.
- The Docker image copies that skill into `/app/.claude/skills/school-email/SKILL.md` and installs `gws`.
- No MCP server is needed; Claude uses bash + `gws`.
- Development checks: `uv run pyright` and `uv run ruff check .`
- Keep `token.json` out of git if you ever create one locally.

## Docker

Build:
```bash
docker build -t school-email .
```

Run:
```bash
docker run --rm school-email example.com recipient@example.com
```
