import argparse
import asyncio
import logging

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

logger = logging.getLogger(__name__)

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"
SUMMARY_SYSTEM_PROMPT = (
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
SEND_SYSTEM_PROMPT = (
    "Role:\n"
    "You are an email sender. Use Gmail MCP to send the exact email content provided by the user.\n\n"
    "Rules:\n"
    "- Do not rewrite or summarize the message body\n"
    "- Send to exactly the recipient provided\n"
    "- Confirm only after the email is sent\n"
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sender_domain", help="Email domain to match")
    parser.add_argument(
        "recipients",
        nargs="+",
        help="Email address(es) to send the LLM output to",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    return parser.parse_args()


def make_options(system_prompt: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        mcp_servers={
            "gmail": {
                "type": "http",
                "url": GMAIL_MCP_URL,
            }
        },
        effort="low",
        permission_mode="bypassPermissions",
    )


async def main(sender_domain: str, recipients: list[str]):
    options = make_options(SUMMARY_SYSTEM_PROMPT)

    prompt = (
        f"List my emails from the past 7 days only if the sender's email domain "
        f"contains {sender_domain!r}. Do not match on the subject line."
    )

    logger.debug(f"Prompt: {prompt}")
    logger.info("If prompted, complete Google sign-in in the browser.")

    result_chunks = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            result_chunks.append(message.result)
        else:
            logger.debug("[%s]", type(message).__name__)

    result = "\n".join(result_chunks).strip()
    if not result:
        raise RuntimeError("LLM did not return any email summary")
    logger.debug(f"Result: {result}")

    send_options = make_options(SEND_SYSTEM_PROMPT)
    send_prompt = (
        f"Send the following email to these recipients: {', '.join(recipients)}. "
        f"Subject: 'Gmail summary for {sender_domain}'. "
        f"Body must be exactly the text below, with no additions or edits:\n\n{result}"
    )

    async for message in query(prompt=send_prompt, options=send_options):
        if isinstance(message, ResultMessage):
            logger.info("%s", message.result)
        else:
            logger.debug("[%s]", type(message).__name__)

    logger.info(f"Sent summary email to {', '.join(recipients)}")


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
    asyncio.run(main(args.sender_domain, args.recipients))
