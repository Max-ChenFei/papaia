# CIGEva — Object Grounding with LangChain

An agent that detects object bounding boxes in images using [Grounding DINO](https://github.com/IDEA-Research/GroundingDINO), built with [LangChain](https://www.langchain.com) and a local Ollama LLM.

## Prerequisites
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) — pull the model: `ollama run qwen3:0.6b`
- A CUDA-capable GPU for the Grounding tool

## Install
```bash
git clone https://github.com/Max-ChenFei/papaia.git
cd papaia
uv sync --group cigeva
```

## Variants

| Variant | Description |
|---------|-------------|
| [baseline](baseline/) | Tool served manually via FastAPI; agent connects over HTTP |
| [mcp](mcp/) | Tool served via MCP; agent connects using LangChain MCP adapters |
| [ray_serve](ray_serve/) | Tool served via Ray Serve |
| [papaia](papaia/) | Papaia provisions the tool venv automatically |

See each variant's `ReadMe.md` for how to run the agents.
