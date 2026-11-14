# API Reference

This reference documents the user-facing primitives of the **Papaia** package,
organized into four groups: a compute-resource declaration, decorators for
declaring tool runtime requirements, a runtime accelerator-query function, and
the CLI commands. It also covers the extension points for custom executors.


---

## 1. Resource Declaration

Declares the execution nodes available for running tools, together with their
resource capacities, in a TOML file. Each entry states whether the node is
hosted on the agent machine (`local`) or accessed remotely (`remote`). For
remote nodes, it also includes the access details (host, port, user).

The file must contain a `[nodes]` table with one sub-entry per node, and it
**must** define a node named `local`.

```toml
[nodes]
local     = { location = "local",  cpus = 8,  memory = 32 }
vm_berlin = { location = "remote", cpus = 32, memory = 128, accel = "A100:6", host = "172.16.50.171", port = 22, username = "ubuntu" }
```

### Fields

| Field      | Type   | Applies to     | Description                                                                 |
| ---------- | ------ | -------------- | --------------------------------------------------------------------------- |
| `location` | string | all (required) | `"local"` or `"remote"`.                                                    |
| `cpus`     | int    | all (optional) | Number of CPUs the node provides.                                           |
| `memory`   | int    | all (optional) | Memory capacity in GB.                                                       |
| `accel`    | string | all (optional) | Accelerators, as `"<type>:<count>"` (e.g. `"A100:6"`) or `"<type>"` (count 1). |
| `host`     | string | remote (required) | Host address for SSH access.                                             |
| `port`     | int    | remote (optional) | SSH port. Defaults to `22`.                                              |
| `username` | string | remote (required) | SSH user.                                                                |

**Constraints**

- A `[nodes]` table with at least one node is required.
- Exactly one node must be named `local`.
- A node with `location = "remote"` must specify `host` and `username`.

---

## 2. Agent Program Decorators

These decorators annotate a tool with its runtime requirements. They are
*metadata-only*: at import/run time they return the original function or class
unchanged. The Papaia compiler reads the decorator arguments statically (from the
AST) to build each tool's intermediate representation; the requirements are used
for placement and artifact generation, not enforced at decoration time.

### `@required_fn`

Declares runtime requirements for a **function-based** tool.

```python
def required_fn(
    pip_install: str | list[str] | None = None,
    cpus: int | None = None,
    memory: int | None = None,
    accel: str | None = None,
)
```

| Parameter     | Type                       | Description                                                                                          |
| ------------- | -------------------------- | ---------------------------------------------------------------------------------------------------- |
| `pip_install` | `str \| list[str] \| None` | Dependencies. A `str` is treated as a path to a `requirements.txt`; a `list[str]` is a list of pip package specs. |
| `cpus`        | `int \| None`              | Minimum number of CPUs required.                                                                     |
| `memory`      | `int \| None`              | Minimum memory in GB.                                                                                 |
| `accel`       | `str \| None`              | Accelerator requirement, `"<name>:<count>"` or `"<name>"` (count defaults to 1). Example: `"H100:4"`. |

```python
from papaia import required_fn

@required_fn(pip_install=["torch", "transformers"], accel="H100:1")
def caption(image_url: str) -> str:
    ...
```

### `@required_cls`

Declares runtime requirements for a **class-based** (stateful) tool. In addition
to the resource fields, it names the entry method to invoke and optional
lifecycle hooks.

```python
def required_cls(
    entry: str,
    cpus: int | None = None,
    memory: int | None = None,
    pip_install: str | list[str] | None = None,
    accel: str | None = None,
    setup: str | None = None,
    teardown: str | None = None,
)
```

| Parameter     | Type                       | Description                                                                                          |
| ------------- | -------------------------- | ---------------------------------------------------------------------------------------------------- |
| `entry`       | `str` (required)           | Name of the method to invoke as the tool's entry point.                                              |
| `cpus`        | `int \| None`              | Minimum number of CPUs required.                                                                     |
| `memory`      | `int \| None`              | Minimum memory in GB.                                                                                 |
| `pip_install` | `str \| list[str] \| None` | Dependencies (path to `requirements.txt`, or list of pip package specs).                             |
| `accel`       | `str \| None`              | Accelerator requirement, `"<name>:<count>"` or `"<name>"` (count defaults to 1).                     |
| `setup`       | `str \| None`              | Name of an optional setup (lifecycle) method.                                                        |
| `teardown`    | `str \| None`              | Name of an optional teardown (lifecycle) method.                                                     |

```python
from papaia import required_cls, assigned_accel_devices

@required_cls(entry="run", accel="A100:1", pip_install=["groundingdino"])
class Grounding:
    def __init__(self):
        self.ai_model = load_model(weights_path, device=assigned_accel_devices("Grounding"))

    def run(self, image_url: str, target_entity: str):
        return predict(self.ai_model, image_url, target_entity)
```

### Restrictions

Papaia reports the following cases as errors instead of silently running the
tool in the wrong place. The checks apply to every tool, including in-process
ones, so that a tool stays movable when its placement changes:

- **Where tools are defined.** Only tools defined at the top level of the file
  passed to `papaia run` are compiled. Under `papaia run`, a decorated tool
  imported from another module or defined inside a function raises an error
  (best effort: a module that was already imported before the run is not
  re-executed and is therefore not detected).
- **Decorator arguments** must be literals passed by keyword (e.g.,
  `accel="A100:1"`), since the compiler reads them from the source without
  running it. `@required_fn`, `@papaia.required_fn`, and import aliases are
  recognized.
- **Parameters** must be positional-or-keyword; `*args`, `**kwargs`,
  keyword-only, and positional-only parameters are rejected at compile time.

Further restrictions apply when a tool runs out of process (in a local or
remote virtual environment). Respect them for in-process tools as well if the
tool may be moved:

- **Arguments and results** are sent as JSON. Values must be JSON-serializable
  (strings, numbers, booleans, `None`, lists, and dicts), and type annotations
  must be types that Pydantic can validate. Pass large data such as images by
  path or URL. A non-serializable argument raises an exception in the agent;
  tuples arrive as lists and non-string dict keys as strings.
- **Code available to the service.** The generated service contains the tool
  and the file's import statements, which must resolve in the tool's
  environment (i.e., to packages installed via `pip_install`); local modules
  next to the agent program and other module-level functions or variables of
  the file are not copied.
- **Class tools** are instantiated without arguments in the service, and
  their base classes (e.g., LangChain's `BaseTool`) are removed there, so the
  entry, setup, and teardown methods must not rely on inherited behavior.

---

## 3. Runtime Accelerator Query — `assigned_accel_devices`

Returns the accelerator device indices assigned to a named tool at runtime,
enabling device-aware implementations without hard-coding placement decisions.
The compiler injects initialization code that exports the assigned indices as
environment variables; this function reads them back.

```python
def assigned_accel_devices(name: str) -> str | None
```

| Parameter | Type  | Description                                                  |
| --------- | ----- | ------------------------------------------------------------ |
| `name`    | `str` | The tool's name (the function or class name it was declared on). |

**Returns:** the assigned device indices as a raw comma-separated string (e.g.
`"0,1"`), or `None` if no accelerator was assigned to that tool.

**Raises:** `ValueError` if `name` is an empty string.

For device-agnostic tool code, `assigned_device(name, default="cpu")` returns a
framework device string for the first assigned accelerator (e.g. `"cuda:1"`),
or `default` when none is assigned, so the same tool code runs on nodes with
or without accelerators:

```python
from papaia import assigned_device

model.to(assigned_device("Grounding"))  # "cuda:<i>" on a GPU node, "cpu" otherwise
```

> Indices are communicated via the `TOOL_ACCEL_INDEXES__<name>` environment
> variable so that the assignment is visible across processes.

---

## 4. CLI Commands

Papaia is invoked as a module CLI (`papaia` once installed, or
`python -m papaia`).

### `papaia run`

Compiles an agent program, computes a placement for each tool, deploys and runs
the tools, executes the agent with the standard Python interpreter, and performs
cleanup afterward.

```bash
papaia run path/to/agent.py -c path/to/exec_nodes.toml
```

| Argument         | Description                                                                                              |
| ---------------- | -------------------------------------------------------------------------------------------------------- |
| `file`           | Path to the Python agent program to compile and run. (positional)                                        |
| `--config`, `-c` | Path to the execution-nodes config file. Defaults to `exec_nodes.toml` in the current working directory. |

Behavior: Papaia parses the program into an AST, extracts a per-tool IR, computes
placements, generates and deploys the corresponding artifacts, rewrites the
program so every tool call routes through its generated access stub, and runs the
rewritten program. On completion (including on error) it stops launched services
and removes per-run artifacts.

### `papaia clear`

Removes cached artifacts generated during compilation and execution, including
provisioned Python virtual environments (local and remote).

```bash
papaia clear
```

---

## 5. Programmatic Entry Points

The CLI commands map to importable functions for use from Python.

### `compile_and_run`

```python
def compile_and_run(file_path: Path, nodes_path: Path | None = None) -> None
```

Backs `papaia run`. If `nodes_path` is `None`, looks for `exec_nodes.toml` in the
current directory. Raises `FileNotFoundError` if no valid config is found.

### `clear_cache`

```python
def clear_cache() -> None
```

Backs `papaia clear`. Clears both the remote and local Papaia caches.

---

## 6. Extension — Custom Executors

An **executor** manages the realization and cleanup lifecycle of a tool:
generating its implementation code, deploying it, synthesizing the agent-side
access stub, and tearing it down. Papaia ships three built-in executors selected
automatically by a tool's placement and declared dependencies:

| Executor              | Selected when                                          | Behavior                                                                                  |
| --------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| **in-process**        | Placed on `local` **and** no `pip_install` declared.   | Reuses the original implementation as the stub; runs in the agent process. No service.    |
| **local-venv**        | Placed on `local` **with** `pip_install` declared.     | Wraps the tool in an HTTP service, deploys it in a new local venv, and proxies calls.     |
| **remote-venv**       | Placed on a `remote` node.                             | Same as local-venv, but deploys and runs the service on the remote node over SSH.         |

### Registering a custom executor

```python
from papaia import add_executor, Executor

def add_executor(name: str, executor: Executor) -> None
```

Registers `executor` under `name`. Raises `ValueError` if the name is already
registered.

### The `Executor` interface

Custom executors subclass `Executor` (an `ABC`) and implement two methods:

```python
class Executor(ABC):
    def _generate_code(self, desc) -> tuple[list[str] | None, str | None, str]:
        """Return (pip_install, generated_code, invoke_template).
        invoke_template is a string.Template; `url` is substituted as base_url."""
        ...

    def _deploy(self, node, desc, generated_code: str) -> str:
        """Deploy the artifact and return its access URL (or a falsy value for
        in-process). Keep the tool's callable signature intact."""
        ...
```

The base class's `run(node, desc)` orchestrates these: it generates code, appends
the declared dependencies, deploys (off the event loop), and substitutes the
returned URL into the invoke template to produce the access stub. `stop(name)`
releases assigned accelerator devices and clears per-tool state during cleanup.
