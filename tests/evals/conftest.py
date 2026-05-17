import base64
import json
import os
import textwrap

import pytest


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def _make_gws_script(data: dict) -> str:
    """Return a self-contained Python script that acts as a fake gws CLI."""
    data_json = json.dumps(data)
    return textwrap.dedent(f"""\
        #!/usr/bin/env python3
        import json, sys

        DATA = {data_json}

        args = sys.argv[1:]
        joined = " ".join(args)

        if "--help" in args or "schema" in args:
            print("gws mock - schema inspection not needed in eval mode")
            sys.exit(0)

        if "list" in joined:
            print(json.dumps(DATA.get("list", {{"messages": []}})))
        elif "get" in joined:
            for i, a in enumerate(args):
                if a == "--params" and i + 1 < len(args):
                    try:
                        params = json.loads(args[i + 1])
                        msg_id = params.get("id", "")
                        print(json.dumps(DATA["messages"].get(msg_id, {{}})))
                    except Exception:
                        print("{{}}")
                    sys.exit(0)
            print("{{}}")
        elif "send" in joined:
            print(json.dumps({{"id": "SENT_MOCK", "labelIds": ["SENT"]}}))
        else:
            print("{{}}")

        sys.exit(0)
    """)


def _install_gws(monkeypatch, tmp_path, data: dict) -> None:
    script = tmp_path / "gws"
    script.write_text(_make_gws_script(data))
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")


@pytest.fixture
def mock_gws_two_emails(monkeypatch, tmp_path):
    """Two school emails: one with a link (MSG001, May 14 UTC), one without (MSG002, May 10 UTC)."""
    body1 = _b64(
        "Dear parents, please sign the permission slip at "
        "https://forms.school.com/fieldtrip by Friday."
    )
    body2 = _b64(
        "The school board meeting is next Monday at 7pm in the gymnasium."
    )
    data = {
        "list": {
            "messages": [
                {"id": "MSG001", "threadId": "T001"},
                {"id": "MSG002", "threadId": "T002"},
            ]
        },
        "messages": {
            "MSG001": {
                "id": "MSG001",
                "snippet": "Please sign the permission slip for the upcoming field trip.",
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [
                        {"name": "From", "value": "Teacher <teacher@school.com>"},
                        {"name": "Subject", "value": "Field trip permission slip"},
                        {"name": "Date", "value": "Thu, 14 May 2026 20:00:00 +0000"},
                    ],
                    "body": {"size": len(body1), "data": body1},
                },
            },
            "MSG002": {
                "id": "MSG002",
                "snippet": "Board meeting next Monday at 7pm.",
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [
                        {"name": "From", "value": "Principal <principal@school.com>"},
                        {"name": "Subject", "value": "Board meeting next Monday"},
                        {"name": "Date", "value": "Sun, 10 May 2026 15:00:00 +0000"},
                    ],
                    "body": {"size": len(body2), "data": body2},
                },
            },
        },
    }
    _install_gws(monkeypatch, tmp_path, data)
    return data


@pytest.fixture
def mock_gws_empty(monkeypatch, tmp_path):
    """Gmail returns no matching messages."""
    data = {"list": {"messages": []}, "messages": {}}
    _install_gws(monkeypatch, tmp_path, data)
    return data


@pytest.fixture
def mock_gws_tz_boundary(monkeypatch, tmp_path):
    """Email received at 06:00 UTC = 23:00 PDT (UTC-7) on May 14.
    The correct PT date is 2026-05-14, not the UTC date 2026-05-15.
    """
    body = _b64("Reminder: school is closed tomorrow for a staff development day.")
    data = {
        "list": {"messages": [{"id": "TZ001", "threadId": "T001"}]},
        "messages": {
            "TZ001": {
                "id": "TZ001",
                "snippet": "School closed tomorrow for staff development day.",
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [
                        {"name": "From", "value": "Office <office@school.com>"},
                        {"name": "Subject", "value": "School closed tomorrow"},
                        # 2026-05-15 06:00 UTC = 2026-05-14 23:00 PDT (UTC-7)
                        {"name": "Date", "value": "Fri, 15 May 2026 06:00:00 +0000"},
                    ],
                    "body": {"size": len(body), "data": body},
                },
            }
        },
    }
    _install_gws(monkeypatch, tmp_path, data)
    return data
