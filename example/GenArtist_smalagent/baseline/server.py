import tempfile
import requests
import torch
from diffusers import StableDiffusionXLPipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Web Server for hosting Text2Image Tool")

pipe = StableDiffusionXLPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
pipe = pipe.to("cuda:0")

def text2image(text: str, height: int = 1024, width: int = 1024) -> str:
    image = pipe(text, height=height, width=width).images[0]
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp.name)
        with open(tmp.name, "rb") as f:
            res = requests.post("https://tmpfile.link/api/upload", files={"file": f})
        res.raise_for_status()
    return res.json()["downloadLink"]


class Text2ImageRequest(BaseModel):
    text: str
    height: int = 1024
    width: int = 1024


class Text2ImageResponse(BaseModel):
    result: str


@app.post("/text2image", response_model=Text2ImageResponse)
def text2image_endpoint(payload: Text2ImageRequest):
    try:
        result = text2image(payload.text, payload.height, payload.width)
        return Text2ImageResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
