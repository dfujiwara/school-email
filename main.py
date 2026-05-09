import asyncio
import argparse

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sender_domain", help="Email domain to match")
    return parser.parse_args()


async def main(sender_domain: str):
    options = ClaudeAgentOptions(
        mcp_servers={
            "gmail": {
                "type": "http",
                "url": GMAIL_MCP_URL,
            }
        },
        permission_mode="bypassPermissions",
    )

    prompt = (
        f"List my emails from the past 7 days only if the sender's email domain "
        f"contains {sender_domain!r}. Do not match on the subject line. "
        f"Return only a Markdown list with one bullet per email and no extra text. "
        f"Each bullet must include sender, subject, a short summary, and any links mentioned. "
        f"If there are no links, write 'Links: None'."
    )

    print(f"Prompt: {prompt}\n")
    print("If prompted, complete Google sign-in in the browser.\n")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            print(message.result)
        else:
            print(f"[{type(message).__name__}]")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.sender_domain))
