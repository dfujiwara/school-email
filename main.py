import argparse
import asyncio
import logging

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

logger = logging.getLogger(__name__)

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"
SYSTEM_PROMPT = (
    "Role:\n"
    "You are an email summarizer. Process batches of emails and provide concise, accurate summaries.\n\n"
    "Focus:\n"
    "- Sender\n"
    "- Subject\n"
    "- Short summary of the email\n"
    "- Links mentioned (if any)\n\n"
    "Output format:\n"
    "- Return strictly the Markdown list as the complete response\n"
    "- Use one bullet per email\n"
    "- Do not include any extra text, headings, code fences, or commentary\n"
    "- If there are no links, write 'Links: None'\n"
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sender_domain", help="Email domain to match")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    return parser.parse_args()


async def main(sender_domain: str):
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={
            "gmail": {
                "type": "http",
                "url": GMAIL_MCP_URL,
            }
        },
        effort="low",
        permission_mode="bypassPermissions",
    )

    prompt = (
        f"List my emails from the past 7 days only if the sender's email domain "
        f"contains {sender_domain!r}. Do not match on the subject line."
    )

    logger.debug("Prompt: %s", prompt)
    logger.info("If prompted, complete Google sign-in in the browser.")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            logger.info("%s", message.result)
        else:
            logger.debug("[%s]", type(message).__name__)


LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=LOG_LEVELS[args.log_level], format="%(message)s")
    asyncio.run(main(args.sender_domain))
