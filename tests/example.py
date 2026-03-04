from decl import required_fn
from langchain.tools import tool
from langchain.agents import create_agent


@tool
@required_fn(accel="A100:1")
def get_weather(city: str) -> str:
    """Get weather for a given city.
    Args:
        city: The city to get the weather for.
    """
    return f"It's always sunny in {city}!"


agent = create_agent(model="openai", tools=[get_weather])

agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in Berlin?"}]}
)
