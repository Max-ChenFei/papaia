from fastmcp import FastMCP

import tempfile
import requests
import torch
from diffusers import StableDiffusionXLPipeline


mcp = FastMCP("MCP Server for Hosting Grounding Tool")

pipe = StableDiffusionXLPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
pipe = pipe.to("cuda:0")


@mcp.tool
def text2image(text: str, height: int = 1024, width: int = 1024) -> str:
    image = pipe(text, height=height, width=width).images[0]
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp.name)
        with open(tmp.name, "rb") as f:
            res = requests.post("https://tmpfile.link/api/upload", files={"file": f})
        res.raise_for_status()
    return res.json()["downloadLink"]
