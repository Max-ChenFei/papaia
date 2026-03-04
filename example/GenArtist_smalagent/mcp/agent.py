from smolagents import OpenAIModel, ToolCallingAgent, MCPClient
import gradio as gr


client = MCPClient({"url": "http://localhost:43141/mcp", "transport": "streamable-http"})
tools = client.get_tools()

model = OpenAIModel(model_id="qwen3:0.6b", api_base="http://localhost:11434/v1", api_key="ollama")
agent = ToolCallingAgent(tools=tools, model=model)


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


