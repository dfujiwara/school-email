import asyncio

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


async def main():
    prompt = "What is 2 + 2? Answer in one sentence."
    options = ClaudeAgentOptions(permission_mode="bypassPermissions")

    print(f"Prompt: {prompt}\n")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            print(f"Result: {message.result}")
        else:
            print(f"[{type(message).__name__}]")


if __name__ == "__main__":
    asyncio.run(main())
