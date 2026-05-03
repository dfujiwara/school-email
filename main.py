import asyncio

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"


async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "gmail": {
                "type": "http",
                "url": GMAIL_MCP_URL,
            }
        },
        permission_mode="bypassPermissions",
    )

    prompt = "List my 5 most recent emails with their subjects and senders."

    print(f"Prompt: {prompt}\n")
    print("If prompted, complete Google sign-in in the browser.\n")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            print(f"Result: {message.result}")
        else:
            print(f"[{type(message).__name__}]")


if __name__ == "__main__":
    asyncio.run(main())
