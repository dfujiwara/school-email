import pytest

from main import render_summary


def test_sorts_newest_first(sample_payload):
    result = render_summary(sample_payload)
    assert result.index("2026-05-14") < result.index("2026-05-10")


def test_includes_all_fields(sample_payload):
    result = render_summary(sample_payload)
    assert "Field trip permission slip" in result
    assert "teacher@school.com" in result
    assert "forms.school.com" in result


def test_empty_returns_no_match_message():
    assert render_summary({"emails": []}) == "No matching emails found in the past 7 days."


def test_no_links_renders_none(sample_payload):
    sample_payload["emails"][1]["links"] = []
    result = render_summary(sample_payload)
    assert "None" in result


def test_links_rendered(sample_payload):
    result = render_summary(sample_payload)
    assert "https://forms.school.com/fieldtrip" in result


def test_missing_emails_key_raises():
    with pytest.raises(ValueError):
        render_summary({})


def test_non_dict_item_raises():
    with pytest.raises(ValueError):
        render_summary({"emails": ["not a dict"]})


def test_invalid_date_raises():
    with pytest.raises(ValueError):
        render_summary(
            {
                "emails": [
                    {
                        "sender": "s@school.com",
                        "received_date": "not-a-date",
                        "subject": "Test",
                        "summary": "A summary.",
                        "links": [],
                    }
                ]
            }
        )


def test_missing_received_date_raises():
    with pytest.raises(ValueError):
        render_summary(
            {
                "emails": [
                    {
                        "sender": "s@school.com",
                        "subject": "Test",
                        "summary": "A summary.",
                        "links": [],
                    }
                ]
            }
        )
