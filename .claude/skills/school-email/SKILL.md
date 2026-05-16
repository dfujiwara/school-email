---
name: school-email
description: Query Gmail for recent mail from a sender domain, summarize it, and send an HTML email summary.
---

# school-email

## Goal

Given a sender domain and one or more recipients:
1. Query Gmail for the last 7 days using a `q` that includes `newer_than:7d` and `from:<sender_domain>`.
2. Fetch message metadata for the returned IDs.
3. Summarize the results.
4. Send the summary as HTML email.

## Prerequisites

- `gws` is installed and authenticated.
- Before calling a Gmail method, inspect it:
  - `gws gmail --help`
  - `gws schema gmail.users.messages.list`
  - `gws schema gmail.users.messages.get`
  - `gws schema gmail.users.messages.send`

## Workflow

### 1) List recent messages
Use a single canonical Gmail search query:

```bash
gws gmail users messages list --params '{"userId":"me","q":"newer_than:7d from:example.com","maxResults":100}'
```

If an extra filter is needed, append it to the same `q` string:

```bash
gws gmail users messages list --params '{"userId":"me","q":"newer_than:7d from:example.com is:unread","maxResults":100}'
```

### 2) Fetch headers for each message
For each message ID, fetch metadata with `From`, `Subject`, and `Date` headers:

```bash
gws gmail users messages get --params '{"userId":"me","id":"MESSAGE_ID","format":"metadata","metadataHeaders":["From","Subject","Date"]}'
```

### 3) Summarize
- Extract sender, received date, subject, short summary, and links if available.
- Sort the final set in reverse chronological order.
- If Gmail returned any unexpected messages, discard them before summarizing.

### 4) Send the summary
Send an HTML email to the requested recipients using Gmail send. Build the exact request shape from the schema output.

### 5) Safety
- Do not reveal tokens or credentials.
- Keep the email body and recipients exactly as requested.
- If the environment is missing `gws`, fail clearly and tell the user how to install it.
