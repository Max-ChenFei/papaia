

<h1 align="center">papaia</h1>

<p align="center">
<a href="https://github.com/Max-ChenFei/papaia/actions/workflows/test.yml"><img src="https://github.com/Max-ChenFei/papaia/actions/workflows/test.yml/badge.svg?branch=main" alt="unit tests"></a>
<a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
</p>

<p align="center">
<em>A Python package for simplifying the integration of tools into AI agents.</em>
</p>

As agents integrate a broader mix of tools, ranging from compute-light utilities (e.g., web search) to tools backed by compute-intensive model inference (e.g., diffusion-based models), the runtime requirements of these tools vary in both computational demand and package dependencies. In conventional implementations, developers manually place each tool by deciding whether it remains in process or is externalized to a separate process or remote node, in order to satisfy compute constraints and avoid dependency conflicts, thereby triggering a domino effect of heterogeneous implementations, transport-coupled invocation, and duplicated interface definitions. 


With Papaia Python package, developers declare compute resources and tools' runtime requirements; the compiler generates the corresponding placement-specific artifacts.

## User-Facing Primitives

### Execution Nodes

- `@exec_nodes.toml`


Declares the available execution nodes and their resource capacities in a configuration file.

### Agent Program

- `@required_fn`
- `@required_cls`

These decorators declare tool interfaces together with their runtime requirements (e.g., accelerator type, memory constraints).

- `assigned_accel_devices`

This API allows a tool to query the accelerator devices assigned to it at runtime, enabling device-aware implementations without hard-coding placement decisions.

### Compiler Interface

- `papaia run`  
  Derives a feasible realization of the declared tools—including placement and invocation strategy—and executes the agent program.

- `papaia clear`  
  Removes cached artifacts generated during compilation and execution, including provisioned virtual Python environments.

## Examples

The [`example/`](./example) directory contains self-contained example programs illustrating typical usage of the programming model. Each example demonstrates:

- declaring tools using `@required_fn` or `@required_cls`,
- accessing assigned runtime resources via the runtime API, and
- executing an agent program through the `papaia` compiler interface.

## Development
For `papaia`  
```bash
uv sync
```

For `unit tests`
```bash
uv sync --group test
uv run pytest
```
