import argparse
import asyncio
import logging

from claude_agent_sdk import ResultMessage, query

from main import make_options, markdown_to_html, send_summary_email
from prompts import DOC_SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize an attached document from a Gmail email"
    )
    parser.add_argument(
        "search_query",
        help="Gmail search query to find the email with the attachment (e.g. 'subject:report has:attachment')",
    )
    parser.add_argument(
        "recipients",
        nargs="*",
        help="Optional email address(es) to send the summary to",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    return parser.parse_args()


async def summarize_doc(search_query: str) -> str:
    options = make_options(DOC_SUMMARY_SYSTEM_PROMPT)

    prompt = (
        f"Find the most recent email matching this Gmail search query: {search_query!r}. "
        f"If the email has an attachment (document, PDF, spreadsheet, etc.), read its contents "
        f"and provide a detailed summary of the document."
    )

    logger.debug(f"Prompt: {prompt}")
    logger.info("If prompted, complete Google sign-in in the browser.")

    summary = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            summary = message.result
            logger.debug(f"Result: {summary!r}")
        else:
            logger.debug("[%s]", type(message).__name__)

    if not summary:
        raise RuntimeError("LLM did not return a summary")

    return summary


async def main(search_query: str, recipients: list[str]) -> None:
    summary = await summarize_doc(search_query)
    print(summary)

    if recipients:
        html_body = markdown_to_html(summary)
        await send_summary_email(search_query, recipients, html_body)


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(
        level=LOG_LEVELS[args.log_level],
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main(args.search_query, args.recipients))
