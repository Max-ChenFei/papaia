# Quick start: a Google ADK agent with a local LLM (no GPU, no API key)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Max-ChenFei/papaia/blob/main/use_cases/adk_ollama/quickstart.ipynb)

This is the example of the [Quick Start](../../README.md#quick-start) in the main README.
`factor` is declared with `@required_fn(pip_install=["sympy"])`, so Papaia runs it in its own virtual environment; ADK sees only the generated stub.
The LLM is `qwen3:1.7b`, served locally by [Ollama](https://ollama.com) on the CPU.

```bash
ollama pull qwen3:1.7b
cd use_cases/adk_ollama
uv run --project ../.. --with "google-adk==2.14.1" --with "litellm==1.109.1" papaia run agent.py -c exec_nodes.toml
```

`quickstart.ipynb` runs the same example in Google Colab.
