import tempfile
from typing import Any, Dict

import requests
import torch
from diffusers import StableDiffusionXLPipeline
from langchain.agents import create_agent
from langchain.tools import BaseTool
from langchain_ollama import ChatOllama

from declagent import assigned_accel_devices, required_cls


@required_cls(
    entry="_run",
    accel="RTX 8000",
    pip_install=[
        "torch --index-url https://download.pytorch.org/whl/cu124",
        "git+https://github.com/Max-ChenFei/declagent.git",
        "transformers",
        "diffusers",
        "Pillow",
        "requests",
    ],
)
class Text2Image(BaseTool):
    name: str = "text2image"
    description: str = (
        "Generate images from text descriptions and return URL of generated image."
    )
    args_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "text prompt"},
            "height": {"type": "integer", "default": 1024},
            "width": {"type": "integer", "default": 1024},
        },
        "required": ["text"],
    }
    _pipe: Any = None

    def _get_pipe(self):
        if self._pipe is None:
            assigned_device = assigned_accel_devices("Text2Image")
            if assigned_device is not None:
                device = f"cuda:{assigned_device}"
            else:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            pipe = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
            )
            self._pipe = pipe.to(device)
        return self._pipe

    def _run(self, text: str, height: int = 1024, width: int = 1024) -> str:
        pipe = self._get_pipe()
        image = pipe(text, height=height, width=width).images[0]
        print("Image generated, uploading...")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            # Upload directly to file hosting service (e.g., tflink for demo purposes)
            with open(tmp.name, "rb") as f:
                res = requests.post(
                    "https://tmpfile.link/api/upload", files={"file": f}
                )
            res.raise_for_status()  # error if failed
        return res.json()["downloadLink"]


llm = ChatOllama(model="qwen3:0.6b", validate_model_on_init=True, temperature=0)
agent = create_agent(
    model=llm, tools=[Text2Image()], system_prompt="You are a helpful assistant."
)
text = "Small silhouette of a climber on an enormous black cliff, endless vertical wall, minimal composition, extreme scale contrast, monochrome, symbol of resilience and discipline"
prompt = f"""You must call the text2image tool with the argument 'text': {text} to generate an image. Return only the URL of the image without any extra text."""
result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
print(result["messages"][-1].content)
