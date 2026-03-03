from typing import List
import requests
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_ollama import ChatOllama


@tool("grounding")
def grounding_proxy(image_url: str, labels: List[str], threshold: float = 0.3):
    """Return bounding boxes for target entities in the image."

    Args:
        image_url: image url.
        labels: minItems is 1.
        threshold: Default value is 0.3. Minimum score required to keep a label. Must be in [0.0, 1.0].
    """
    payload = {"image_url": image_url, "labels": labels, "threshold": threshold}
    response = requests.post("http://localhost:52273/grounding", json=payload, timeout=60)
    if response.status_code != 200:
        error_detail = (
            response.json().get("detail", response.text)
            if response.headers.get("content-type") == "application/json"
            else response.text
        )
        raise Exception(f"Server error ({response.status_code}): {error_detail}")
    return response.json()["result"]


llm = ChatOllama(model="qwen3:0.6b", validate_model_on_init=True, temperature=0)
agent = create_agent(model=llm, tools=[grounding_proxy], system_prompt="You are a helpful assistant.")
image_url = "http://images.cocodataset.org/val2017/000000039769.jpg"
prompt = f"Call the grounding tool with image_url={image_url}, labels=['cat'], threshold=0.3 and list all detected bounding boxes separately."
result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
print(result["messages"][-1].content)
