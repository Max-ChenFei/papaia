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

Declare the execution nodes available for running tools in a compute-resource declaration (`exec_nodes.toml`):

```toml
# exec_nodes.toml
[nodes.local]
location = "local"
cpus = 8
memory = 32
```

Declare each tool's runtime requirements with a decorator and write your program in ordinary Python (`agent.py`):

```python
from papaia import required_fn

@required_fn(pip_install=["sympy"])
def factor(expression: str) -> str:
    """Factor a polynomial expression."""
    import sympy
    return str(sympy.factor(expression))

print(factor("x**2 - 1"))  # in an agent, register `factor` as a tool instead
```

Compile, place, deploy, and run the program with a single command:

```bash
papaia run agent.py -c exec_nodes.toml
```

This runs without a GPU or a remote node: `factor` runs in its own virtual environment with `sympy` installed, so `sympy` is not needed in the agent's environment, and the program prints `(x - 1)*(x + 1)`.

To see the same tool used by an agent with a local LLM, run the [ADK quick start](./use_cases/adk_ollama) or open it in [Colab](https://colab.research.google.com/github/Max-ChenFei/papaia/blob/main/use_cases/adk_ollama/quickstart.ipynb).

## Examples

| Example | Framework | Shows | Needs |
|---|---|---|---|
| [`adk_ollama`](./use_cases/adk_ollama) | Google ADK | An agent with a local LLM calling a Papaia tool that runs in its own environment; also runnable in [Colab](https://colab.research.google.com/github/Max-ChenFei/papaia/blob/main/use_cases/adk_ollama/quickstart.ipynb) | Ollama with `qwen3:0.6b` (CPU only); no GPU, no API key |
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
