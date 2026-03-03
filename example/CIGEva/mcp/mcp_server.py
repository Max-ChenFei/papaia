from fastmcp import FastMCP
from io import BytesIO
import requests
from PIL import Image
from transformers import pipeline
from typing import List

mcp = FastMCP("MCP Server for Hosting Grounding Tool")

detector = pipeline(model="IDEA-Research/grounding-dino-tiny", task="zero-shot-object-detection", device="cuda:0")


@mcp.tool
def grounding(image_url: str, labels: List[str], threshold: float = 0.3):
    img = Image.open(BytesIO(requests.get(image_url).content)).convert("RGB")
    labels = [label if label.endswith(".") else label + "." for label in labels]
    results = detector(img, candidate_labels=labels, threshold=threshold)
    return [result["box"] for result in results]
