SUMMARY_OUTPUT_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "emails": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sender": {"type": "string"},
                        "received_date": {
                            "type": "string",
                            "description": "Date only (YYYY-MM-DD) in Pacific Time",
                        },
                        "subject": {"type": "string"},
                        "summary": {"type": "string"},
                        "links": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "sender",
                        "received_date",
                        "subject",
                        "summary",
                        "links",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["emails"],
        "additionalProperties": False,
    },
}

SUMMARY_SYSTEM_PROMPT = (
    "Role:\n"
    "You are an email summarizer.\n\n"
    "Output rules:\n"
    "- Return ONLY valid JSON\n"
    "- Do not wrap it in markdown, code fences, or commentary\n"
    "- Do not include any text before or after the JSON\n\n"
    "The response must be an object with a single key: emails\n"
    "- emails: array of objects\n"
    "- Each object must have sender, received_date, subject, summary, links\n"
    "- received_date must be date-only in Pacific Time, formatted as YYYY-MM-DD\n"
    "- Normalize the email received timestamp to Pacific Time before taking the date\n"
    "- links must be an array of strings\n"
    "- Use [] for links when there are none\n\n"
    "Example:\n"
    "{\n"
    '  "emails": [\n'
    "    {\n"
    '      "sender": "Example Sender <sender@example.com>",\n'
    '      "received_date": "2026-05-08",\n'
    '      "subject": "Example subject",\n'
    '      "summary": "Brief summary of the email.",\n'
    '      "links": ["https://example.com"]\n'
    "    }\n"
    "  ]\n"
    "}\n"
)

DOC_SUMMARY_SYSTEM_PROMPT = (
    "Role:\n"
    "You are a document summarizer with access to Gmail via MCP.\n\n"
    "Task:\n"
    "- Use Gmail MCP to find the email matching the user's search query\n"
    "- Retrieve the full thread content including any attachments\n"
    "- Read the attachment content and provide a clear, structured summary\n\n"
    "Output rules:\n"
    "- Return a well-structured plain-text summary\n"
    "- Include the document title/filename, main topics, key points, and any action items\n"
    "- If no matching email is found, say so clearly\n"
    "- If the email has no attachment, summarize the email body instead and note there was no attachment\n"
)

SEND_SYSTEM_PROMPT = (
    "Role:\n"
    "You are an email sender. Use Gmail MCP to send the exact email content provided by the user.\n\n"
    "Rules:\n"
    "- Do not rewrite, summarize, or alter the message body\n"
    "- Preserve the HTML exactly as provided\n"
    "- Send to exactly the recipient provided\n"
    "- Confirm only after the email is sent\n"
)
