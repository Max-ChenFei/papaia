import tempfile
import requests
import torch
from diffusers import StableDiffusionXLPipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Text2Image:
    def __init__(self):
        self._pipe = None

    def _get_pipe(self):
        if self._pipe is None:
            device = "cuda:0"
            pipe = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
            )
            self._pipe = pipe.to(device)
        return self._pipe

    def forward(self, text: str, height: int = 1024, width: int = 1024) -> str:
        pipe = self._get_pipe()
        image = pipe(text, height=height, width=width).images[0]
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            with open(tmp.name, "rb") as f:
                res = requests.post(
                    "https://tmpfile.link/api/upload", files={"file": f}
                )
            res.raise_for_status()
        return res.json()["downloadLink"]


instance = Text2Image()


class Text2ImageRequest(BaseModel):
    text: str
    height: int = 1024
    width: int = 1024


class Text2ImageResponse(BaseModel):
    result: str


@app.post("/text2image", response_model=Text2ImageResponse)
def text2image_endpoint(payload: Text2ImageRequest):
    try:
        result = instance.forward(payload.text, payload.height, payload.width)
        return Text2ImageResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import sys
    import traceback

    try:
        print(f"Starting FastAPI server on port 43141...", flush=True)
        uvicorn.run(app, host="0.0.0.0", port=43141, log_level="info")
    except Exception as e:
        print(f"FATAL ERROR starting server: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
