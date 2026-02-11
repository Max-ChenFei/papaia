from io import BytesIO
from typing import Any, List
import requests
from PIL import Image
from transformers import pipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Grounding:
    _detector: Any = None

    def _get_detector(self):
        if self._detector is None:
            device = "cuda:0"
            self._detector = pipeline(
                model="IDEA-Research/grounding-dino-tiny",
                task="zero-shot-object-detection",
                device=device,
            )
        return self._detector

    def _run(self, image_url: str, labels: List[str], threshold: float = 0.3):
        img = Image.open(BytesIO(requests.get(image_url).content)).convert("RGB")
        labels = [label if label.endswith(".") else label + "." for label in labels]
        detector = self._get_detector()
        results = detector(img, candidate_labels=labels, threshold=threshold)
        return [result["box"] for result in results]


instance = Grounding()
app = FastAPI()


class GroundingRequest(BaseModel):
    image_url: str
    labels: List[str]
    threshold: float = 0.3


class GroundingResponse(BaseModel):
    result: Any


@app.post("/grounding", response_model=GroundingResponse)
def grounding_endpoint(payload: GroundingRequest):
    try:
        result = instance._run(payload.image_url, payload.labels, payload.threshold)
        return GroundingResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import sys
    import traceback

    try:
        uvicorn.run(app, host="0.0.0.0", port=52273, log_level="info")
    except Exception as e:
        print(f"FATAL ERROR starting server: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
