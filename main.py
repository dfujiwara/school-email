import asyncio
import os

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"


async def main():
    access_token = os.environ.get("GMAIL_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("GMAIL_ACCESS_TOKEN environment variable is not set")

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
