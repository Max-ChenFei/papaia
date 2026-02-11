import requests
import torch
import gradio as gr
from diffusers import StableDiffusionXLPipeline
from smolagents import Tool, OpenAIModel
from smolagents import ToolCallingAgent
from declagent import assigned_accel_devices


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
        self._pipe = None

    def _get_pipe(self):
        if self._pipe is None:
            device = f"cuda:{assigned_accel_devices('Text2Image')}"
            pipe = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
            )
            self._pipe = pipe.to(device)
        return self._pipe

    def forward(self, text: str, height: int = 1024, width: int = 1024) -> str:
        url = "http://172.30.162.209:41519/text2image"
        payload = {"text": text, "height": height, "width": width}
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            error_detail = (
                response.json().get("detail", response.text)
                if response.headers.get("content-type") == "application/json"
                else response.text
            )
            raise Exception(f"Server error ({response.status_code}): {error_detail}")
        return response.json()["result"]


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
