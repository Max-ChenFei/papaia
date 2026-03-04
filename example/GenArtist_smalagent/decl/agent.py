import requests
import gradio as gr
from smolagents import Tool, OpenAIModel
from smolagents import ToolCallingAgent
import tempfile
import torch
from diffusers import StableDiffusionXLPipeline

from decl import assigned_accel_devices, required_cls


@required_cls(
    entry="forward",
    accel="RTX 8000",
    pip_install=[
        "torch --index-url https://download.pytorch.org/whl/cu124",
        "git+https://github.com/Max-ChenFei/decl.git",
        "transformers",
        "diffusers",
        "Pillow",
        "requests",
    ],
)
class Text2Image(Tool):
    name = "text2image"
    description = (
        "Generate images from text descriptions and return URL of generated image."
    )

    inputs = {
        "text": {"type": "string", "description": "text prompt"},
        "height": {
            "type": "integer",
            "description": "Image height in pixels",
            "default": 1024,
            "nullable": True,
        },
        "width": {
            "type": "integer",
            "description": "Image width in pixels",
            "default": 1024,
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        pipe = StableDiffusionXLPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
        self._pipe = pipe.to(f"cuda:{assigned_accel_devices('Text2Image')}")


    def forward(self, text: str, height: int = 1024, width: int = 1024) -> str:
        image = self._pipe(text, height=height, width=width).images[0]
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            with open(tmp.name, "rb") as f:
                res = requests.post(
                    "https://tmpfile.link/api/upload", files={"file": f}
                )
            res.raise_for_status()
        return res.json()["downloadLink"]


model = OpenAIModel(
    model_id="qwen3:0.6b", api_base="http://localhost:11434/v1", api_key="ollama"
)
agent = ToolCallingAgent(tools=[Text2Image()], model=model)


def chat_with_agent(message, history):
    try:
        result = agent.run(message)
        if (
            isinstance(result, str)
            and result.startswith("http://")
            or result.startswith("https://")
        ):
            return f"![Generated Image]({result})\n\nImage URL: {result}"
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


demo = gr.ChatInterface(
    fn=chat_with_agent,
    title="Image Generation Agent",
    description="Ask me to generate images! Try: 'Generate an image of a sunset over mountains'",
    examples=[
        "Generate an image of a futuristic city at night",
        "Create a picture of a cat wearing a wizard hat",
        "Small silhouette of a climber on an enormous black cliff, endless vertical wall, minimal composition",
    ],
)

if __name__ == "__main__":
    demo.launch(share=False)
