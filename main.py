import asyncio
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"
TOKEN_FILE = Path(__file__).parent / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


def get_access_token() -> str:
    if not TOKEN_FILE.exists():
        raise FileNotFoundError("token.json not found — run scripts/auth.py first")

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())

    return creds.token


async def main():
    access_token = get_access_token()

    options = ClaudeAgentOptions(
        mcp_servers={
            "gmail": {
                "type": "http",
                "url": GMAIL_MCP_URL,
                "headers": {"Authorization": f"Bearer {access_token}"},
            }
        },
        permission_mode="bypassPermissions",
    )

    prompt = "List my 5 most recent emails with their subjects and senders."

    print(f"Prompt: {prompt}\n")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            print(f"Result: {message.result}")
        else:
            print(f"[{type(message).__name__}]")


if __name__ == "__main__":
    asyncio.run(main())
