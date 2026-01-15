from langchain.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent


from single_spec import required


@required(env="python:3.9-slim")
@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


# Install ollama model and "ollama run qwen2.5:1.5b" to start the local server
llm = ChatOllama(
    model="qwen2.5:1.5b",
    validate_model_on_init=True,
    temperature=0,
)

agent = create_agent(
    model=llm,
    tools=[get_weather],
    system_prompt="You are a helpful assistant and call the get_weather tool when needed.",
)

# Run the agent with a user query
result = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

print(result["messages"][-1].content)
