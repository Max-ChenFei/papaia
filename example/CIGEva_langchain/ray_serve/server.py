from ray import serve

from io import BytesIO
import requests
from PIL import Image
from transformers import pipeline
from fastapi import FastAPI, Body

app = FastAPI(title="Web Server for hosting Grounding Tool")


@serve.deployment(ray_actor_options={"num_gpus": 1})
@serve.ingress(app)
class Grounding:
    def __init__(self):
        self.detector = pipeline(model="IDEA-Research/grounding-dino-tiny", task="zero-shot-object-detection", device="cuda:0")

    @app.post("/grounding")
    def run(self, payload: dict = Body(...)):
        img = Image.open(BytesIO(requests.get(payload["image_url"]).content)).convert("RGB")
        labels = [l if l.endswith(".") else l + "." for l in payload["labels"]]
        threshold = float(payload.get("threshold", 0.3))
        results = self.detector(img, candidate_labels=labels, threshold=threshold)
        return [result["box"] for result in results]


deployment = Grounding.bind()
