"""
Offline AI evals for the email summarisation pipeline.

These tests load pre-captured Claude outputs from tests/evals/captured/ and
score them against correctness criteria. No API calls are made; the tests
run in normal CI like any other unit test.

To refresh the captured files after a model or prompt change, run:
    uv run tests/evals/generate_captures.py

What is evaluated
-----------------
Schema compliance   All required fields present with correct types.
Date format         received_date is YYYY-MM-DD, not localised or long-form.
Timezone accuracy   Email at 06:00 UTC = 23:00 PDT → date must be the PT date.
Link extraction     URLs in email bodies appear in the links array.
Summary quality     Summaries are non-empty strings.
Empty handling      Zero messages from Gmail → empty emails array.
"""
import json
import re
from pathlib import Path

import pytest

CAPTURES = Path(__file__).parent / "captured"
REQUIRED_FIELDS = {"sender", "received_date", "subject", "summary", "links"}


def load(name: str) -> dict:
    return json.loads((CAPTURES / f"{name}.json").read_text())


# ---------------------------------------------------------------------------
# Schema compliance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["two_emails", "tz_boundary", "empty_result"])
def test_has_emails_array(name):
    data = load(name)
    assert "emails" in data, f"{name}: missing 'emails' key"
    assert isinstance(data["emails"], list), f"{name}: 'emails' must be a list"


@pytest.mark.parametrize("name", ["two_emails", "tz_boundary"])
def test_all_required_fields_present(name):
    for email in load(name)["emails"]:
        missing = REQUIRED_FIELDS - email.keys()
        assert not missing, f"{name}: email missing fields {missing}"


@pytest.mark.parametrize("name", ["two_emails", "tz_boundary"])
def test_links_is_list(name):
    for email in load(name)["emails"]:
        assert isinstance(email["links"], list), (
            f"{name}: 'links' for {email.get('subject')!r} must be a list"
        )


# ---------------------------------------------------------------------------
# Date format
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["two_emails", "tz_boundary"])
def test_received_date_is_iso_format(name):
    for email in load(name)["emails"]:
        date = email["received_date"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", date), (
            f"{name}: received_date {date!r} is not YYYY-MM-DD"
        )


def test_timezone_normalization():
    """Email header: 'Fri, 15 May 2026 06:00:00 +0000' (UTC).
    06:00 UTC = 23:00 PDT (UTC-7), so the Pacific date is 2026-05-14.
    A naive UTC extraction would incorrectly produce 2026-05-15.
    """
    emails = load("tz_boundary")["emails"]
    assert len(emails) == 1
    got = emails[0]["received_date"]
    assert got == "2026-05-14", (
        f"Expected PT date 2026-05-14, got {got!r}. "
        "Regenerate with generate_captures.py to see current model behaviour."
    )


# ---------------------------------------------------------------------------
# Content quality
# ---------------------------------------------------------------------------


def test_two_emails_count():
    assert len(load("two_emails")["emails"]) == 2


def test_link_extracted_from_body():
    """URL embedded in the MSG001 body must appear in the links array."""
    all_links = [
        link
        for email in load("two_emails")["emails"]
        for link in email["links"]
    ]
    assert any("forms.school.com/fieldtrip" in link for link in all_links), (
        f"Expected forms.school.com/fieldtrip in links. Got: {all_links}"
    )


@pytest.mark.parametrize("name", ["two_emails", "tz_boundary"])
def test_summaries_are_non_empty(name):
    for email in load(name)["emails"]:
        assert email["summary"].strip(), (
            f"{name}: empty summary for {email.get('subject')!r}"
        )


def test_empty_result():
    assert load("empty_result")["emails"] == []
