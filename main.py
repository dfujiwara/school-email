import argparse
import asyncio
import json
import logging
from datetime import date
from pprint import pformat

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
from claude_agent_sdk.types import HookContext, HookInput, HookJSONOutput, HookMatcher
from markdown_it import MarkdownIt

from prompts import SEND_SYSTEM_PROMPT, SUMMARY_OUTPUT_FORMAT, SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

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


def format_log_data(data: object) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except TypeError:
        return pformat(data, sort_dicts=False)


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


async def log_pre_tool_use(
    hook_input: HookInput, tool_use_id: str | None, context: HookContext
) -> HookJSONOutput:
    logger.debug(f"PreToolUse input:\n{format_log_data(hook_input)}")
    return {"continue_": True}


async def log_post_tool_use(
    hook_input: HookInput, tool_use_id: str | None, context: HookContext
) -> HookJSONOutput:
    logger.debug(f"PostToolUse input:\n{format_log_data(hook_input)}")
    return {"continue_": True}


def make_options(
    system_prompt: str, output_format: dict[str, object] | None = None
) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        tools={"type": "preset", "preset": "claude_code"},
        allowed_tools=["Bash"],
        skills=["school-email"],
        effort="low",
        permission_mode="dontAsk",
        output_format=output_format,
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[log_pre_tool_use])],
            "PostToolUse": [HookMatcher(matcher="Bash", hooks=[log_post_tool_use])],
        },
    )


def render_summary(payload: dict[str, object]) -> str:
    logger.debug(f"Parsed payload:\n{format_log_data(payload)}")
    items = payload.get("emails")
    if items is None or not isinstance(items, list):
        raise ValueError("Summary response must contain an emails array")

    if not items:
        return "No matching emails found in the past 7 days."

    logger.debug(f"Email count: {len(items)}")
    validated_items: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each summary item must be a JSON object")
        validated_items.append(item)

    def received_date_sort_key(item: dict[str, object]) -> date:
        received_date = item.get("received_date")
        if not isinstance(received_date, str):
            raise ValueError("Each summary item must include a received_date string")
        try:
            return date.fromisoformat(received_date)
        except ValueError as exc:
            raise ValueError(f"Invalid received_date: {received_date!r}") from exc

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
        f"Use gws Gmail search with a query that includes newer_than:7d and from:{sender_domain}. "
        f"Do not match on the subject line. Return ONLY valid JSON in the exact shape {{\"emails\": [...]}} with no explanation, greeting, markdown, or extra text. "
        f"If no emails match, return {{\"emails\": []}}."
    )

    logger.debug(f"Prompt: {prompt}")
    logger.info("If prompted, complete Google sign-in in the browser.")

    structured_result = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            structured_result = message.structured_output
            logger.debug(f"structured_output:\n{format_log_data(structured_result)}")
        else:
            logger.debug(f"[{type(message).__name__}]")

    if not isinstance(structured_result, dict):
        raise RuntimeError("LLM did not return structured output")

    logger.debug(
        "Emails structured output:\n%s",
        json.dumps(structured_result, indent=2, ensure_ascii=False),
    )
    markdown_body = render_summary(structured_result)
    html_body = markdown_to_html(markdown_body)
    logger.debug(f"Markdown body:\n{markdown_body}")
    logger.debug(f"HTML body:\n{html_body}")
    return html_body


async def send_summary_email(
    sender_domain: str, recipients: list[str], html_body: str
) -> None:
    send_options = make_options(SEND_SYSTEM_PROMPT)
    send_prompt = (
        f"Send the following email to these recipients: {', '.join(recipients)}. "
        f"Subject: 'Gmail summary for {sender_domain}'. "
        f"Body must be exactly the HTML email below, with no additions or edits:\n\n{html_body}"
    )

    async for message in query(prompt=send_prompt, options=send_options):
        if isinstance(message, ResultMessage):
            logger.info(f"{message.result}")
        else:
            logger.debug(f"[{type(message).__name__}]")

    logger.info(f"Sent summary email to {', '.join(recipients)}")


async def main(sender_domain: str, recipients: list[str]):
    await send_summary_email(
        sender_domain, recipients, await generate_summary_html(sender_domain)
    )


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
