import asyncio
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from papaia import required_fn

@required_fn(pip_install=["sympy"])
def factor(expression: str) -> str:
    """Factor a polynomial expression.

    Args:
        expression: A polynomial, e.g. "x**2 - 1".
    """
    import sympy
    return str(sympy.factor(expression))

# Register the tool with an ADK agent as usual (running the agent needs a Gemini API key).
agent = Agent(name="math", model="gemini-2.0-flash", tools=[factor])

# Without an API key: show the declaration ADK sends to the LLM and call the tool through ADK.
tool = FunctionTool(factor)
print("Declaration:", tool._get_declaration())
print("Result:", asyncio.run(tool.run_async(args={"expression": "x**2 - 1"}, tool_context=None)))
