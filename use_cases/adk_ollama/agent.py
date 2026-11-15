"""Quick start: a Google ADK agent with one Papaia tool, a local LLM, no GPU, no API key."""

import asyncio
import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

from papaia import required_fn


@required_fn(pip_install=["sympy"])
def factor(expression: str) -> str:
    """Factor a polynomial expression.

    Args:
        expression: A polynomial in Python syntax, e.g. "x**2 - 1".
    """
    import sys

    import sympy

    return f"{sympy.factor(expression)} (computed in the environment {sys.prefix})"


agent = Agent(
    name="math_assistant",
    model=LiteLlm(model="ollama_chat/" + os.environ.get("MODEL", "qwen3:0.6b")),
    instruction="You are a math assistant. Always call the factor tool to factor a polynomial; never factor it yourself. /no_think",
    tools=[factor],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)


async def main() -> None:
    runner = InMemoryRunner(agent=agent, app_name="quickstart")
    session = await runner.session_service.create_session(app_name="quickstart", user_id="user")
    question = types.Content(role="user", parts=[types.Part(text="Factor x**2 - 1.")])
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=question):
        for part in event.content.parts if event.content and event.content.parts else []:
            if part.function_call:
                print(f"[tool call]   {part.function_call.name}({part.function_call.args})")
            if part.function_response:
                print(f"[tool result] {part.function_response.response}")
            if part.text and not part.thought and event.is_final_response():
                print("\nANSWER:", part.text.strip())


asyncio.run(main())
