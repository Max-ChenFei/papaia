from langchain.tools import BaseTool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent


from single_spec import required_cls


@required_cls(env="python:3.9-slim", entry="_run")
class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = "Get weather for a given city."

    def _run(self, city: str) -> str:
        return f"It's always sunny in {city}!"


# Install ollama model and "ollama run qwen2.5:1.5b" to start the local server
llm = ChatOllama(
    model="qwen2.5:1.5b",
    validate_model_on_init=True,
    temperature=0,
)

agent = create_agent(
    model=llm,
    tools=[WeatherTool()],
    system_prompt="You are a helpful assistant and call the get_weather tool when needed.",
)

# Run the agent with a user query
result = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

print(result["messages"][-1].content)
