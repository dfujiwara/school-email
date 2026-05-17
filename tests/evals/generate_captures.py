"""
Regenerate the captured Claude outputs used by the offline evals.

Run after any change to the model, system prompt, or output schema:

    uv run tests/evals/generate_captures.py

Requires ANTHROPIC_API_KEY. Overwrites tests/evals/captured/*.json.
The refreshed files should be reviewed and committed so the offline tests
reflect the current model's actual behaviour.
"""
import asyncio
import base64
import json
import os
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

# Resolve project root so this script can be run from any directory.
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from claude_agent_sdk import ResultMessage, query  # noqa: E402
from main import make_options  # noqa: E402
from prompts import SUMMARY_OUTPUT_FORMAT, SUMMARY_SYSTEM_PROMPT  # noqa: E402

CAPTURES_DIR = Path(__file__).parent / "captured"

# Exact prompt used by generate_summary_html() in main.py.
_PROMPT = (
    "Use gws Gmail search with a query that includes newer_than:7d and from:{domain}. "
    "Do not match on the subject line. Return ONLY valid JSON in the exact shape "
    '{"emails": [...]} with no explanation, greeting, markdown, or extra text. '
    'If no emails match, return {"emails": []}.'
)


# ---------------------------------------------------------------------------
# Mock gws helpers (mirrors tests/evals/conftest.py)
# ---------------------------------------------------------------------------


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def _make_gws_script(data: dict) -> str:
    data_json = json.dumps(data)
    return textwrap.dedent(f"""\
        #!/usr/bin/env python3
        import json, sys

        DATA = {data_json}

        args = sys.argv[1:]
        joined = " ".join(args)

        if "--help" in args or "schema" in args:
            print("gws mock")
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


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {
    "two_emails": {
        "domain": "school.com",
        "data": {
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
                        "body": {
                            "data": _b64(
                                "Dear parents, please sign the permission slip at "
                                "https://forms.school.com/fieldtrip by Friday."
                            )
                        },
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
                        "body": {
                            "data": _b64(
                                "The school board meeting is next Monday at 7pm in the gymnasium."
                            )
                        },
                    },
                },
            },
        },
    },
    "tz_boundary": {
        "domain": "school.com",
        "data": {
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
                        "body": {
                            "data": _b64(
                                "Reminder: school is closed tomorrow for a staff development day."
                            )
                        },
                    },
                }
            },
        },
    },
    "empty_result": {
        "domain": "school.com",
        "data": {"list": {"messages": []}, "messages": {}},
    },
}


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


async def capture(name: str, domain: str, gws_data: dict) -> None:
    tmp = tempfile.mkdtemp()
    try:
        script = Path(tmp) / "gws"
        script.write_text(_make_gws_script(gws_data))
        script.chmod(0o755)

        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmp}:{old_path}"
        try:
            options = make_options(SUMMARY_SYSTEM_PROMPT, SUMMARY_OUTPUT_FORMAT)
            structured_result = None
            async for message in query(prompt=_PROMPT.format(domain=domain), options=options):
                if isinstance(message, ResultMessage):
                    structured_result = message.structured_output
        finally:
            os.environ["PATH"] = old_path
    finally:
        shutil.rmtree(tmp)

    out = CAPTURES_DIR / f"{name}.json"
    out.write_text(json.dumps(structured_result, indent=2, ensure_ascii=False) + "\n")
    print(f"  [{name}] saved → {out}")


async def main() -> None:
    CAPTURES_DIR.mkdir(exist_ok=True)
    for name, scenario in SCENARIOS.items():
        print(f"Generating {name}...")
        await capture(name, scenario["domain"], scenario["data"])
    print("Done. Review the diffs in captured/ before committing.")


if __name__ == "__main__":
    asyncio.run(main())
