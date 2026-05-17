"""
AI eval tests for generate_summary_html().

These tests run the real Claude agent against a mock gws CLI, then validate the
structured output for correctness. They require ANTHROPIC_API_KEY and make real
API calls. Run explicitly with:

    pytest -m eval

The mock_gws_* fixtures create a fake `gws` binary at the front of PATH.
Claude's bash calls hit that instead of real Gmail, giving us deterministic
inputs while still exercising the full prompt and extraction logic.

What is evaluated:
  - Schema compliance: Claude returns valid JSON matching the output_format schema
  - Date format: all dates are YYYY-MM-DD (not localized or reformatted)
  - Link extraction: URLs found in email bodies appear in the HTML output
  - Empty result handling: no messages → "No matching emails" message
  - Timezone normalization: UTC timestamps are converted to Pacific Time before
    extracting the date (a common failure mode)
"""
import re

import pytest

from main import generate_summary_html

pytestmark = pytest.mark.eval


async def test_produces_html_for_two_emails(mock_gws_two_emails):
    """Claude returns non-empty HTML when two emails exist."""
    html = await generate_summary_html("school.com")
    assert html.strip(), "Expected non-empty HTML output"
    assert "<html" in html.lower(), "Output should be an HTML document"


async def test_dates_are_iso_format(mock_gws_two_emails):
    """All dates in the output are YYYY-MM-DD; no US-style (MM/DD/YYYY) or long-form dates."""
    html = await generate_summary_html("school.com")
    # Flag any date-looking strings that are NOT ISO format
    non_iso = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", html)
    assert not non_iso, f"Non-ISO dates found: {non_iso}"
    long_form = re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d+, \d{4}\b", html)
    assert not long_form, f"Long-form dates found: {long_form}"


async def test_links_extracted_from_email_body(mock_gws_two_emails):
    """A URL present in an email body appears in the rendered HTML output."""
    html = await generate_summary_html("school.com")
    assert "forms.school.com/fieldtrip" in html, (
        "Expected link from MSG001 body not found in output.\n"
        f"Output (first 800 chars):\n{html[:800]}"
    )


async def test_empty_result_shows_no_match_message(mock_gws_empty):
    """When Gmail returns no messages, the output says no emails were found."""
    html = await generate_summary_html("school.com")
    assert "No matching emails" in html, (
        f"Expected 'No matching emails' in output.\nGot: {html[:400]}"
    )


async def test_timezone_normalization_to_pacific(mock_gws_tz_boundary):
    """Email at 2026-05-15 06:00 UTC = 2026-05-14 23:00 PDT.
    Claude must report the PT date (2026-05-14), not the UTC date (2026-05-15).
    """
    html = await generate_summary_html("school.com")
    assert "2026-05-14" in html, (
        "Expected PT date 2026-05-14 for an email received at 06:00 UTC "
        "(= 23:00 PDT on May 14). Claude may be using the UTC date instead.\n"
        f"Output (first 800 chars):\n{html[:800]}"
    )
