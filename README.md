<h1 align="center">papaia</h1>

<p align="center">
<a href="https://github.com/Max-ChenFei/papaia/actions/workflows/test.yml"><img src="https://github.com/Max-ChenFei/papaia/actions/workflows/test.yml/badge.svg?branch=main" alt="unit tests"></a>
<a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
<a href="./docs/api-reference.md"><img src="https://img.shields.io/badge/docs-API%20reference-blue.svg" alt="Docs"></a>
<a href="https://colab.research.google.com/github/Max-ChenFei/papaia/blob/main/use_cases/adk_ollama/quickstart.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab"></a>
</p>

<p align="center">
<em>A Python package for simplifying the integration of tools into AI agents.</em>
</p>

With **Papaia**, developers declare compute resources and each tool's runtime requirements—without manually deciding where each tool runs, writing the corresponding implementation, wiring transport-coupled invocation, or duplicating interface definitions across artifacts. A compiler pipeline derives tool placements from these declarations and generates the corresponding placement-specific artifacts.

## Installation

Papaia requires Python ≥ 3.11, < 3.14.

Install the latest version from GitHub:

```bash
pip install git+https://github.com/Max-ChenFei/papaia.git
```

<!-- Once published to PyPI:
```bash
pip install papaia
```
-->

## Quick Start

This quick demo shows how Papaia simplifies tool integration in a Google ADK agent. the LLM runs locally with Ollama and no GPU needed.

You can run it in your browser in [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Max-ChenFei/papaia/blob/main/use_cases/adk_ollama/quickstart.ipynb), or locally with the steps below (the files are in [`use_cases/adk_ollama`](./use_cases/adk_ollama)).

The agent has one tool, `factor`, which needs `sympy`. Papaia automatically places the tool in its own virtual environment not the same progress with the agent program on the same execution node.

**1. Install** Papaia, Google ADK, and [Ollama](https://ollama.com/download), and download the model (about 1.4 GB):

```bash
pip install "git+https://github.com/Max-ChenFei/papaia.git" "google-adk==2.14.1" "litellm==1.109.1"
ollama pull qwen3:1.7b
```

**2. Declare the compute resources** available for running tools (`exec_nodes.toml`):

```toml
# One local node: no GPU, no remote machine.
[nodes.local]
location = "local"
cpus = 2
memory = 4
```

**3. Declare each tool's runtime requirements** with a decorator, and write the agent as usual (`agent.py`):

```python
import asyncio

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

from papaia import required_fn


@required_fn(pip_install=["sympy"])
def factor(expression: str) -> str:
    """Factor a polynomial expression.

    Args:
        expression: A polynomial in Python syntax, e.g. "x**2 - 1".
    """
    import sys
    import sympy
    return f"{sympy.factor(expression)} (computed in {sys.prefix})"


agent = Agent(
    name="math_assistant",
    model=LiteLlm(model="ollama_chat/qwen3:1.7b", think=False),  # local LLM served by Ollama
    instruction="You are a math assistant. Always call the factor tool to factor a polynomial; never factor it yourself.",
    tools=[factor],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)
asyncio.run(InMemoryRunner(agent=agent).run_debug("Factor x**2 - 1.", verbose=True))
```

**4. Compile, place, deploy, and run** the agent with a single command:

```bash
papaia run agent.py -c exec_nodes.toml
```

The agent calls `factor`, which runs in its own environment under `.papaia_cache/factor/`:

```
math_assistant > [Calling tool: factor({'expression': 'x**2 - 1'})]
math_assistant > [Tool result: {'result': '(x - 1)*(x + 1) (computed in .../.papaia_cache/factor/.venv)'}]
math_assistant > The factored form of $ x^2 - 1 $ is $ (x - 1)(x + 1) $.
```

## Examples

| Example | Framework | Shows | Needs |
|---|---|---|---|
| [`adk_ollama`](./use_cases/adk_ollama) | Google ADK | The Quick Start: an agent with a local LLM calling a Papaia tool that runs in its own environment; also runnable in [Colab](https://colab.research.google.com/github/Max-ChenFei/papaia/blob/main/use_cases/adk_ollama/quickstart.ipynb) | Ollama with `qwen3:1.7b` (CPU only); no GPU, no API key |
| [`weather_demo_docker`](./use_cases/weather_demo_docker) | LangChain | Moving a tool between a local and a remote node by changing only the compute-resource declaration | Docker and internet access: simulates a local and a remote GPU node; no GPU, no API key |
| [`CIGEva_langchain`](./use_cases/CIGEva_langchain) | LangChain | Case study from the paper, with baseline, Ray Serve, and MCP versions for comparison | GPU (local or remote), Ollama |
| [`GenArtist_smalagent`](./use_cases/GenArtist_smalagent) | smolagents | Case study from the paper, with baseline, Ray Serve, and MCP versions for comparison | GPU (local or remote), Ollama |

## Documentation

See the [API Reference](./docs/api-reference.md) for the user-facing primitives, CLI commands, full signatures and parameters, and the custom-executor extension API.

## Testing

To run the unit tests locally:

```bash
uv sync --group test && uv run pytest
```

Unit tests also run on every push to any branch and on every pull request via [GitHub Actions](https://github.com/Max-ChenFei/papaia/actions/workflows/test.yml).

## Issues and Contributing

Questions, bug reports, and feature requests are welcome! Please open an issue in [GitHub Issues](https://github.com/Max-ChenFei/papaia/issues) to share your feedback. Before creating a new issue, check whether a similar one already exists. For bug reports, include the steps to reproduce the problem, your Python and Papaia versions, and the full error message.

Pull requests are welcome.

## Citation

Papaia is currently under review. Citation details (BibTeX) will be added here once it is accepted.

## License

Released under the [MIT License](./LICENSE).
