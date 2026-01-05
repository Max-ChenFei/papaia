import ast
from dataclasses import dataclass

from .env import Env


@dataclass(frozen=True)
class Metadata:
    """Runtime metadata for a function or class.

    Attributes:
        env: Runtime environment.
        cpus: Number of CPUs at least.
        memory: Memory specification in GB at least.
        accel: Accelerator requirement. Format: "<name>:<count>" or "<name>"
            (defaults to a count of 1). Example: "H100:4".
        entry: Class only. Entry method name.
        setup: Class only. Setup method name.
        teardown: Class only. Teardown method name.
    """

    env: Env | None = None
    cpus: int | None = None
    memory: int | None = None
    accel: str | None = None

    # lifecycle (class-only)
    entry: str | None = None
    setup: str | None = None
    teardown: str | None = None


def extract_metadata(decorator: ast.Call, is_class_def: bool) -> Metadata | None:
    """Extract Metadata from a single decorator AST node."""
    env = None
    cpus = None
    memory = None
    accel = None
    entry = None
    setup = None
    teardown = None

    for keyword in decorator.keywords:
        if keyword.arg == "env":
            env = ast.literal_eval(keyword.value)
        elif keyword.arg == "cpus":
            cpus = ast.literal_eval(keyword.value)
        elif keyword.arg == "memory":
            memory = ast.literal_eval(keyword.value)
        elif keyword.arg == "accel":
            accel = ast.literal_eval(keyword.value)
        elif is_class_def:
            if keyword.arg == "entry":
                entry = ast.literal_eval(keyword.value)
            elif keyword.arg == "setup":
                setup = ast.literal_eval(keyword.value)
            elif keyword.arg == "teardown":
                teardown = ast.literal_eval(keyword.value)

    if not is_class_def:
        if env is None and accel is None and cpus is None and memory is None:
            return None
        else:
            return Metadata(env, cpus, memory, accel)
    if entry is None:
        raise ValueError("Class metadata must specify 'entry' method.")
    return Metadata(
        env,
        cpus,
        memory,
        accel,
        entry,
        setup,
        teardown,
    )
