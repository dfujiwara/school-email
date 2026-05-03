import asyncio
from pprint import pformat

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

    sender_domain = "Piedmont"
    prompt = (
        f"List my 5 most recent emails only if the sender's email domain "
        f"contains {sender_domain!r}. Do not match on the subject line. "
        f"Return each email's subject and sender."
    )

    print(f"Prompt: {prompt}\n")
    print("If prompted, complete Google sign-in in the browser.\n")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            print(f"Result: {message.result}")
            print(
                "Summary: "
                f"stop_reason={message.stop_reason!r}, "
                f"turns={message.num_turns}, "
                f"cost=${message.total_cost_usd or 0:.4f}"
            )
        else:
            details = getattr(message, "__dict__", None) or {}
            print(f"[{type(message).__name__}] {pformat(details)}")


if __name__ == "__main__":
    asyncio.run(main())
