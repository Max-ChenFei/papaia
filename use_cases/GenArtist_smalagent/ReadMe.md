# GenArtist — Image Generation with smolagents

A Gradio chat agent that generates images using [Stable Diffusion XL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0), built with [smolagents](https://github.com/huggingface/smolagents) and a local Ollama LLM. The use case compares four tool-deployment strategies.

## Prerequisites
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) — pull the model: `ollama run qwen3:0.6b`
- A CUDA-capable GPU (e.g., RTX 8000 or RTX 4090) for image generation

## Install
```bash
git clone https://github.com/Max-ChenFei/papaia.git
cd papaia
uv sync --group genartist
```

## Variants

| Variant | Description |
|---------|-------------|
| [baseline](baseline/) | Tool served manually via FastAPI; agent connects over HTTP |
| [mcp](mcp/) | Tool served via MCP; agent connects using smolagents MCP client |
| [ray_serve](ray_serve/) | Tool served via Ray Serve |
| [papaia](papaia/) | Papaia provisions the tool venv automatically |

See each variant's `ReadMe.md` for how to run the agents.
