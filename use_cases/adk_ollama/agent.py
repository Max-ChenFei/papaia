import asyncio

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

    return f"{sympy.factor(expression)} (computed in {sys.prefix})"


agent = Agent(
    name="math_assistant",
    model=LiteLlm(model="ollama_chat/qwen3:1.7b", think=False),  # local LLM served by Ollama
    instruction="You are a math assistant. Always call the factor tool to factor a polynomial; never factor it yourself.",
    tools=[factor],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)
asyncio.run(InMemoryRunner(agent=agent).run_debug("Factor x**2 - 1.", verbose=True))
