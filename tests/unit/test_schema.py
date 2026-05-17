import json

import pytest
from pydantic import BaseModel, ValidationError


class EmailItem(BaseModel):
    sender: str
    received_date: str
    subject: str
    summary: str
    links: list[str]


class EmailsOutput(BaseModel):
    emails: list[EmailItem]


def test_valid_payload_passes_schema(sample_payload):
    EmailsOutput.model_validate(sample_payload)


def test_empty_emails_passes_schema():
    EmailsOutput.model_validate({"emails": []})


def test_missing_emails_key_fails_schema():
    with pytest.raises(ValidationError):
        EmailsOutput.model_validate({})


def test_missing_required_field_fails_schema():
    with pytest.raises(ValidationError):
        EmailsOutput.model_validate(
            {
                "emails": [
                    {
                        "sender": "s@school.com",
                        "received_date": "2026-05-10",
                        # subject missing
                        "summary": "A summary.",
                        "links": [],
                    }
                ]
            }
        )


def test_wrong_links_type_fails_schema():
    with pytest.raises(ValidationError):
        EmailsOutput.model_validate(
            {
                "emails": [
                    {
                        "sender": "s@school.com",
                        "received_date": "2026-05-10",
                        "subject": "Test",
                        "summary": "A summary.",
                        "links": "https://example.com",  # should be a list
                    }
                ]
            }
        )


def test_json_string_roundtrip(sample_payload):
    EmailsOutput.model_validate_json(json.dumps(sample_payload))


def test_invalid_json_fails():
    with pytest.raises(Exception):
        EmailsOutput.model_validate_json("not json")
