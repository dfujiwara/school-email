import argparse
import asyncio
import logging
from datetime import date

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
from markdown_it import MarkdownIt

from prompts import SEND_SYSTEM_PROMPT, SUMMARY_OUTPUT_FORMAT, SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

GMAIL_MCP_URL = "https://gmailmcp.googleapis.com/mcp/v1"
MARKDOWN_CONVERTER = MarkdownIt()
EMAIL_HTML_TEMPLATE = """<!doctype html>
<html>
  <body style="margin:0;padding:24px;font-family:Arial,Helvetica,sans-serif;line-height:1.5;color:#111;">
    <div style="max-width:720px;margin:0 auto;">
      {content}
    </div>
  </body>
</html>
"""


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

    def received_date_sort_key(item: dict[str, object]) -> date:
        received_date = item.get("received_date")
        if isinstance(received_date, str):
            try:
                return date.fromisoformat(received_date)
            except ValueError:
                pass
        return date.min

    logger.debug(f"Email count: {len(items)}")
    validated_items: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each summary item must be a JSON object")
        validated_items.append(item)

    validated_items.sort(key=received_date_sort_key, reverse=True)

    blocks = []
    for item in validated_items:
        sender = item.get("sender", "Unknown sender")
        received_date = item.get("received_date", "Unknown date")
        subject = item.get("subject", "(no subject)")
        summary = item.get("summary", "")
        links = item.get("links", [])
        if not isinstance(links, list):
            links = [str(links)]

        links_block = (
            "\n".join(f"  - {link}" for link in links) if links else "  - None"
        )
        blocks.append(
            f"### {subject}\n"
            f"- **Date:** {received_date}\n"
            f"- **From:** {sender}\n"
            f"- **Summary:** {summary}\n"
            f"- **Links:**\n{links_block}"
        )

    return "\n\n".join(blocks)


def markdown_to_html(markdown_text: str) -> str:
    content = MARKDOWN_CONVERTER.render(markdown_text)
    return EMAIL_HTML_TEMPLATE.format(content=content)


async def generate_summary_html(sender_domain: str) -> str:
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

    markdown_body = render_summary(structured_result)
    html_body = markdown_to_html(markdown_body)
    logger.debug(f"Markdown body: {markdown_body}")
    logger.debug(f"HTML body: {html_body}")
    return html_body


async def send_summary_email(
    sender_domain: str, recipients: list[str], html_body: str
) -> None:
    send_options = make_options(SEND_SYSTEM_PROMPT)
    send_prompt = (
        f"Send the following email to these recipients: {', '.join(recipients)}. "
        f"Subject: 'Email summary from {sender_domain}'. "
        f"Body must be exactly the HTML email below, with no additions or edits:\n\n{html_body}"
    )

    async for message in query(prompt=send_prompt, options=send_options):
        if isinstance(message, ResultMessage):
            logger.info("%s", message.result)
        else:
            logger.debug("[%s]", type(message).__name__)

    logger.info(f"Sent summary email to {', '.join(recipients)}")


async def main(sender_domain: str, recipients: list[str]):
    html_body = await generate_summary_html(sender_domain)
    await send_summary_email(sender_domain, recipients, html_body)


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
