import requests
import gradio as gr
from smolagents import tool, OpenAIModel
from smolagents import ToolCallingAgent


@tool(name="text2image")
def text2image_proxy(text: str, height: int = 1024, width: int = 1024) -> str:
    """Generate images from text descriptions and return URL of generated image.


    Args:
        text: text prompt.
        height: Image height in pixels, default is 1024.
        width: Image width in pixels, default is 1024.
    """
    url = "http://172.30.162.209:43141/text2image"
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
agent = ToolCallingAgent(tools=[text2image_proxy], model=model)


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
