import torch
import requests
from PIL import Image
from io import BytesIO
from transformers import pipeline
from typing import List, Any, Dict
from langchain.tools import BaseTool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from single_spec import required_cls


@required_cls(
    pip_install=[
        "torch --index-url https://download.pytorch.org/whl/cu124",
        "transformers",
        "Pillow",
        "requests",
    ],
    accel="RTX 8000",
    entry="_run",
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
        "required": ["image_url", "labels"],
    }
    _detector: Any = None

    def _get_detector(self):
        if self._detector is None:
            # device = assigned_accel_devices("Grounding")
            device = "0"  # For testing purpose, replace with assigned_accel_devices

            # Convert to proper cuda device string
            if device is not None:
                device = f"cuda:{device}"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

            print(f"Using device: {device}")

            self._detector = pipeline(
                model="IDEA-Research/grounding-dino-tiny",
                task="zero-shot-object-detection",
                device=device,
            )
        return self._detector

    def _run(
        self,
        image_url: str,
        labels: List[str],
        threshold: float = 0.3,
    ):
        img = Image.open(BytesIO(requests.get(image_url).content)).convert("RGB")
        labels = [label if label.endswith(".") else label + "." for label in labels]
        detector = self._get_detector()
        results = detector(img, candidate_labels=labels, threshold=threshold)
        return [result["box"] for result in results]


llm = ChatOllama(
    model="qwen3:4b",
    validate_model_on_init=True,
    temperature=0,
)


agent = create_agent(
    model=llm,
    tools=[Grounding()],
    system_prompt="You are a helpful assistant.",
)

# Agent run test
image_url = "http://images.cocodataset.org/val2017/000000039769.jpg"
prompt = f"Call the grounding tool now.\n Use image_url = {image_url}\n labels=['cat'], threshold=0.3."
result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
print(result["messages"][-1].content)
