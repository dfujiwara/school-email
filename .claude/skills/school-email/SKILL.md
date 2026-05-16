---
name: school-email
description: Query Gmail for recent mail from a sender domain, summarize it, and send an HTML email summary.
---

# school-email

Use this skill to reproduce the repository workflow with Google Workspace (`gws`) instead of Gmail MCP.

This skill accepts an optional Gmail search filter parameter.

## Goal

Given a sender domain, optional Gmail filter, and one or more recipients:
1. Find emails from the last 7 days.
2. Apply the Gmail search filter if provided.
3. Keep only messages whose sender email domain contains the requested domain.
4. Sort newest-first.
5. Summarize the results.
6. Send the summary as HTML email.

## Prerequisites

- `gws` is installed and authenticated.
- Before calling a Gmail method, inspect it:
  - `gws gmail --help`
  - `gws schema gmail.users.messages.list`
  - `gws schema gmail.users.messages.get`
  - `gws schema gmail.users.messages.send`

## Workflow

### 1) List recent messages
Use Gmail search for the last 7 days, optionally combining it with a user-provided filter, then inspect the returned message IDs:

```bash
gws gmail users messages list --params '{"userId":"me","q":"newer_than:7d","maxResults":100}'
```

If a filter is provided, merge it into `q`, for example:

```bash
gws gmail users messages list --params '{"userId":"me","q":"newer_than:7d from:example.com is:unread","maxResults":100}'
```

### 2) Fetch headers for each message
For each message ID, fetch metadata with `From`, `Subject`, and `Date` headers:

```bash
gws gmail users messages get --params '{"userId":"me","id":"MESSAGE_ID","format":"metadata","metadataHeaders":["From","Subject","Date"]}'
```

### 3) Filter and summarize
- Keep only messages where the sender domain contains the requested domain.
- If a Gmail search filter was supplied, apply it when listing messages.
- Extract sender, received date, subject, short summary, and links if available.
- Sort the final set in reverse chronological order.

### 4) Send the summary
Send an HTML email to the requested recipients using Gmail send. Build the exact request shape from the schema output.

### 5) Safety
- Do not reveal tokens or credentials.
- Keep the email body and recipients exactly as requested.
- If the environment is missing `gws`, fail clearly and tell the user how to install it.
