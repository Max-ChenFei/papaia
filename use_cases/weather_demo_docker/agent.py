"""Weather agent: one tool "needs a GPU" (declared only; no real GPU is used).

Which node runs `get_weather` is decided by the execution-node file passed to
`papaia run`; this program is the same in both cases.
"""

import os

from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from papaia import required_fn


@required_fn(accel="A100:1", pip_install=["requests"])
def get_weather(city: str) -> str:
    """Get the current temperature (in Celsius) and wind speed for a city."""
    import socket

    import requests

    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    ).json()["results"][0]
    cur = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "current": "temperature_2m,wind_speed_10m",
        },
        timeout=10,
    ).json()["current"]
    return (
        f"{geo['name']}: {cur['temperature_2m']} C, wind {cur['wind_speed_10m']} km/h "
        f"(tool ran on host '{socket.gethostname()}')"
    )


def current_utc_time() -> str:
    """Return the current UTC time. Runs in the agent process (no declarations)."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


llm = ChatOllama(
    model=os.environ.get("MODEL", "qwen3:0.6b"),
    base_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
    temperature=0,
)
agent = create_agent(
    model=llm,
    tools=[get_weather, current_utc_time],
    system_prompt="You are a helpful assistant. Use the tools to answer.",
)
question = "What is the weather in Berlin now, and what is the current UTC time?"
result = agent.invoke({"messages": [{"role": "user", "content": question}]})

for message in result["messages"]:
    if message.type == "tool":
        print(f"[tool {message.name}] {message.content}")
print("\nANSWER:", result["messages"][-1].content)
