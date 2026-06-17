import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_ollama import ChatOllama


async def run():
    client = MultiServerMCPClient({"grounding": {"transport": "http", "url": "http://localhost:52273/mcp"}})

    tools = await client.get_tools()

    llm = ChatOllama(model="qwen3:0.6b", validate_model_on_init=True, temperature=0)
    agent = create_agent(model=llm, tools=tools, system_prompt="You are a helpful assistant.")
    image_url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    prompt = f"Call the grounding tool with image_url={image_url}, labels=['cat'], threshold=0.3 and list all detected bounding boxes separately."
    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(run())
