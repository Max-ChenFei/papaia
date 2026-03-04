from io import BytesIO
from typing import Any, Dict, List
import requests
from PIL import Image
from transformers import pipeline
from langchain.agents import create_agent
from langchain.tools import BaseTool
from langchain_ollama import ChatOllama

from declagent import assigned_accel_devices, required_cls


@required_cls(entry="_run", accel="RTX 8000", pip_install=[
        "torch --index-url https://download.pytorch.org/whl/cu124",
        "git+https://github.com/Max-ChenFei/declagent.git",
        "transformers",
        "Pillow",
        "requests",
    ],
)
class Grounding(BaseTool):
    name: str = "grounding"
    description: str = "Return bounding boxes for target entities in the image."
    args_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "image_url": {"type": "string", "description": "image url"},
            "labels": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "threshold": {
                "type": "number",
                "default": 0.3,
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
    }
    detector: Any = None

    def __init__(self):
        super().__init__()
        self.detector = pipeline(model="IDEA-Research/grounding-dino-tiny", task="zero-shot-object-detection", device=f"cuda:{assigned_accel_devices('Grounding')}")

    def _run(self, image_url: str, labels: List[str], threshold: float = 0.3):
        img = Image.open(BytesIO(requests.get(image_url).content)).convert("RGB")
        labels = [label if label.endswith(".") else label + "." for label in labels]
        results = self.detector(img, candidate_labels=labels, threshold=threshold)
        return [result["box"] for result in results]



llm = ChatOllama(model="qwen3:0.6b", validate_model_on_init=True, temperature=0)
agent = create_agent(model=llm, tools=[Grounding()], system_prompt="You are a helpful assistant.")
image_url = "http://images.cocodataset.org/val2017/000000039769.jpg"
prompt = f"Call the grounding tool with image_url={image_url}, labels=['cat'], threshold=0.3 and list all detected bounding boxes separately."
result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
print(result["messages"][-1].content)

