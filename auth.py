"""One-time Gmail OAuth flow. Run this once to generate token.json."""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from credentials import load_client_config

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

TOKEN_FILE = Path(__file__).parent / "token.json"


def main():
    client_config = load_client_config()
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json())
    print(f"Token saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
