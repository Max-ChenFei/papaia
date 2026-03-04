# decl

`decl` is a Python package to support the proposed programming mode for building tool-using AI agents in the paper.

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

- `decl run`  
  Derives a feasible realization of the declared tools—including placement and invocation strategy—and executes the agent program.

- `decl clear`  
  Removes cached artifacts generated during compilation and execution, including provisioned virtual Python environments.

## Examples

The [`examples/`](./examples) directory contains self-contained example programs illustrating typical usage of the programming model. Each example demonstrates:

- declaring tools using `@required_fn` or `@required_cls`,
- accessing assigned runtime resources via the runtime API, and
- executing an agent program through the `decl` compiler interface.

