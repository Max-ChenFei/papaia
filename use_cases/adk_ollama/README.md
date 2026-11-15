# Quick start: a Google ADK agent with a local LLM (no GPU, no API key)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Max-ChenFei/papaia/blob/main/use_cases/adk_ollama/quickstart.ipynb)

A Google ADK agent with one tool, `factor`, declared with `@required_fn(pip_install=["sympy"])`.
Papaia places the tool on the local node and runs it in its own virtual environment with `sympy`; ADK sees only the generated stub.
The LLM is `qwen3:0.6b`, served locally by [Ollama](https://ollama.com) on the CPU.

You can run it in the browser with the Colab badge above, or locally:

```bash
# 1. Start Ollama and download the model (about 0.5 GB)
ollama serve &
ollama pull qwen3:0.6b

# 2. Run the agent
cd use_cases/adk_ollama
uv run --project ../.. --with "google-adk==2.14.1" --with "litellm==1.109.1" papaia run agent.py -c exec_nodes.toml
```

Expected output (after the server logs; the environment path differs):
```
[tool call]   factor({'expression': 'x**2 - 1'})
[tool result] {'result': '(x - 1)*(x + 1) (computed in the environment .../.papaia_cache/factor/.venv)'}

ANSWER: The factored form of the polynomial $ x^2 - 1 $ is $ (x - 1)(x + 1) $.
```

The tool result shows that `factor` ran in its own environment. To use another Ollama model, set `MODEL`, e.g. `MODEL=qwen3:1.7b`.
