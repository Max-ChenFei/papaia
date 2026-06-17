from ray import serve

import tempfile
import requests
import torch
from diffusers import StableDiffusionXLPipeline
from fastapi import FastAPI


app = FastAPI(title="Web Server for hosting Text2Image Tool")


@serve.deployment(ray_actor_options={"num_gpus": 1})
@serve.ingress(app)
class Text2Image:
    def __init__(self):
        pipe = StableDiffusionXLPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
        self.pipe = pipe.to("cuda:0")

    @app.post("/text2image")
    def run(self, text: str, height: int = 1024, width: int = 1024) -> str:
        image = self.pipe(text, height=height, width=width).images[0]
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            with open(tmp.name, "rb") as f:
                res = requests.post("https://tmpfile.link/api/upload", files={"file": f})
            res.raise_for_status()
        return res.json()["downloadLink"]

deployment = Text2Image.bind()
