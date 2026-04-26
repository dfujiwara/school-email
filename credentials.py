import base64
import json
import os
from pathlib import Path

CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"


def load_client_config() -> dict:
    raw = os.environ.get("GOOGLE_CREDENTIALS")
    if raw:
        return json.loads(base64.b64decode(raw))
    if CREDENTIALS_FILE.exists():
        return json.loads(CREDENTIALS_FILE.read_text())
    raise FileNotFoundError(
        "No credentials found — set GOOGLE_CREDENTIALS env var or provide credentials.json"
    )
