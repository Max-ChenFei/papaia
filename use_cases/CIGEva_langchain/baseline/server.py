from io import BytesIO
from typing import Any, List
import requests
from PIL import Image
from transformers import pipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Web Server for hosting Grounding Tool")

detector = pipeline(model="IDEA-Research/grounding-dino-tiny", task="zero-shot-object-detection", device="cuda:0")


def grounding(image_url: str, labels: List[str], threshold: float = 0.3):
    img = Image.open(BytesIO(requests.get(image_url).content)).convert("RGB")
    labels = [label if label.endswith(".") else label + "." for label in labels]
    results = detector(img, candidate_labels=labels, threshold=threshold)
    return [result["box"] for result in results]


class GroundingRequest(BaseModel):
    image_url: str
    labels: List[str]
    threshold: float = 0.3


class GroundingResponse(BaseModel):
    result: Any


@app.post("/grounding", response_model=GroundingResponse)
def grounding_endpoint(payload: GroundingRequest):
    try:
        result = grounding(payload.image_url, payload.labels, payload.threshold)
        return GroundingResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
