"""One-time Gmail OAuth flow. Run this once to generate token.json."""

import base64
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

TOKEN_FILE = Path(__file__).parent / "token.json"


def load_client_config() -> dict:
    raw = os.environ.get("GOOGLE_CREDENTIALS")
    if raw:
        return json.loads(base64.b64decode(raw))
    raise EnvironmentError("No credentials found — set GOOGLE_CREDENTIALS env var")


def main():
    client_config = load_client_config()
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json())
    print(f"Token saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
