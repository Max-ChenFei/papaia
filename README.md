<h1 align="center">papaia</h1>

<p align="center">
<a href="https://github.com/Max-ChenFei/papaia/actions/workflows/test.yml"><img src="https://github.com/Max-ChenFei/papaia/actions/workflows/test.yml/badge.svg?branch=main" alt="unit tests"></a>
<a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
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

Declare the execution nodes available for running tools in an `exec_nodes.toml` file:

```toml
# exec_nodes.toml
[nodes.local]
location = "local"
cpus = 8
memory = 32
```

Declare each tool's runtime requirements with a decorator and build your agent in ordinary Python (`agent.py`):

```python
from papaia import required_fn

@required_fn(pip_install=["sympy"])
def factor(expression: str) -> str:
    import sympy
    return str(sympy.factor(expression))

# ... register `factor` with your agent and run it ...
```

Compile, place, deploy, and run the program with a single command:

```bash
papaia run agent.py -c exec_nodes.toml
```

For complete, runnable agents—covering remote GPU tools, accelerator assignment, and class-based tools—see the [`use_cases/`](./use_cases) directory.

## Documentation

See the [API Reference](./docs/api-reference.md) for the user-facing primitives, CLI commands, full signatures and parameters, and the custom-executor extension API.

## Citation

Papaia is currently under review. Citation details (BibTeX) will be added here once it is accepted.

## License

Released under the [MIT License](./LICENSE).
