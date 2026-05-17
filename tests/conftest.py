import pytest


@pytest.fixture
def sample_payload():
    return {
        "emails": [
            {
                "sender": "Teacher <teacher@school.com>",
                "received_date": "2026-05-14",
                "subject": "Field trip permission slip",
                "summary": "Permission slip due May 20 for science museum trip.",
                "links": ["https://forms.school.com/fieldtrip"],
            },
            {
                "sender": "Principal <principal@school.com>",
                "received_date": "2026-05-10",
                "subject": "End of year schedule",
                "summary": "Final exams June 1–5, last day June 10.",
                "links": [],
            },
        ]
    }
