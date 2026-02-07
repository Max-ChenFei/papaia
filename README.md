# declagent

`declagent` is a Python package that serves as the reference implementation of a declarative programming model for building tool-using AI agents.

The model separates *what* a tool does from *where* and *how* it is executed. Developers specify tool semantics and runtime requirements declaratively, while placement, realization, and invocation decisions are deferred to a compiler.

## User-Facing Primitives

### Decorators

- `@required_fn`
- `@required_cls`

These decorators declare tool interfaces together with their runtime requirements (e.g., accelerator type, memory constraints).

### Runtime API

- `assigned_accel_devices`

This API allows a tool to query the accelerator devices assigned to it at runtime, enabling device-aware implementations without hard-coding placement decisions.

### Compiler Interface

- `declagent run`  
  Derives a feasible realization of the declared tools—including placement and invocation strategy—and executes the agent program.

- `declagent clear`  
  Removes cached artifacts generated during compilation and execution, including provisioned virtual Python environments.

## Examples

The [`examples/`](./examples) directory contains self-contained example programs illustrating typical usage of the programming model. Each example demonstrates:

- declaring tools using `@required_fn` or `@required_cls`,
- accessing assigned runtime resources via the runtime API, and
- executing an agent program through the `declagent` compiler interface.
