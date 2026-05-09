import argparse
import asyncio
import logging

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

logger = logging.getLogger(__name__)

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"
SUMMARY_OUTPUT_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "emails": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sender": {"type": "string"},
                        "received_date": {
                            "type": "string",
                            "description": "Date only (YYYY-MM-DD) in Pacific Time",
                        },
                        "subject": {"type": "string"},
                        "summary": {"type": "string"},
                        "links": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "sender",
                        "received_date",
                        "subject",
                        "summary",
                        "links",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["emails"],
        "additionalProperties": False,
    },
}
SUMMARY_SYSTEM_PROMPT = (
    "Role:\n"
    "You are an email summarizer.\n\n"
    "Output rules:\n"
    "- Return ONLY valid JSON\n"
    "- Do not wrap it in markdown, code fences, or commentary\n"
    "- Do not include any text before or after the JSON\n\n"
    "The response must be an object with a single key: emails\n"
    "- emails: array of objects\n"
    "- Each object must have sender, received_date, subject, summary, links\n"
    "- received_date must be date-only in Pacific Time, formatted as YYYY-MM-DD\n"
    "- Normalize the email received timestamp to Pacific Time before taking the date\n"
    "- links must be an array of strings\n"
    "- Use [] for links when there are none\n\n"
    "Example:\n"
    "{\n"
    '  "emails": [\n'
    "    {\n"
    '      "sender": "Example Sender <sender@example.com>",\n'
    '      "received_date": "2026-05-08",\n'
    '      "subject": "Example subject",\n'
    '      "summary": "Brief summary of the email.",\n'
    '      "links": ["https://example.com"]\n'
    "    }\n"
    "  ]\n"
    "}\n"
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


def make_options(
    system_prompt: str, output_format: dict[str, object] | None = None
) -> ClaudeAgentOptions:
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
        output_format=output_format,
    )


def render_summary(payload: dict[str, object]) -> str:
    logger.debug(f"Parsed payload: {payload!r}")
    items = payload.get("emails", [])
    if not isinstance(items, list):
        raise ValueError("Summary response must contain an emails array")

    logger.debug(f"Email count: {len(items)}")
    blocks = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each summary item must be a JSON object")

        sender = item.get("sender", "Unknown sender")
        received_date = item.get("received_date", "Unknown date")
        subject = item.get("subject", "(no subject)")
        summary = item.get("summary", "")
        links = item.get("links", [])
        if not isinstance(links, list):
            links = [str(links)]

        links_text = ", ".join(str(link) for link in links) if links else "None"
        blocks.append(
            f"Received date: {received_date}\n"
            f"Subject: {subject}\n"
            f"Sender: {sender}\n"
            f"Summary: {summary}\n"
            f"Links: {links_text}"
        )

    return "\n\n".join(blocks)


async def main(sender_domain: str, recipients: list[str]):
    options = make_options(SUMMARY_SYSTEM_PROMPT, SUMMARY_OUTPUT_FORMAT)

    prompt = (
        f"Find emails from the past 7 days only if the sender's email domain "
        f'contains {sender_domain!r}. Do not match on the subject line. Return ONLY valid JSON in the exact shape {{"emails": [...]}} with no explanation, greeting, markdown, or extra text. If no emails match, return {{"emails": []}}.'
    )

    logger.debug(f"Prompt: {prompt}")
    logger.info("If prompted, complete Google sign-in in the browser.")

    structured_result = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            structured_result = message.structured_output
            logger.debug(f"structured_output: {structured_result!r}")
        else:
            logger.debug("[%s]", type(message).__name__)

    if not isinstance(structured_result, dict):
        raise RuntimeError("LLM did not return structured output")

    email_body = render_summary(structured_result)
    logger.debug(f"Email body: {email_body}")

    send_options = make_options(SEND_SYSTEM_PROMPT)
    send_prompt = (
        f"Send the following email to these recipients: {', '.join(recipients)}. "
        f"Subject: 'Gmail summary for {sender_domain}'. "
        f"Body must be exactly the text below, with no additions or edits:\n\n{email_body}"
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
    logging.basicConfig(
        level=LOG_LEVELS[args.log_level],
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main(args.sender_domain, args.recipients))
