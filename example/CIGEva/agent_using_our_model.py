import torch
import requests
from PIL import Image
from io import BytesIO
from transformers import pipeline
from typing import List, Any, Dict
from langchain.tools import BaseTool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent


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
        "additionalProperties": False,
    }
    _detector: Any = None

    def _get_detector(self):
        if self._detector is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
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
