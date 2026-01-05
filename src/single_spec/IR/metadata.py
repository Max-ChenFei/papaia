import ast
from dataclasses import dataclass

from .env import Env


@dataclass(frozen=True)
class Metadata:
    """Runtime metadata for a function or class.

    Attributes:
        env: Runtime environment.
        accel: Accelerator requirement. Format: "<name>:<count>" or "<name>"
            (defaults to a count of 1). Example: "H100:4".
        entry: Class only. Entry method name.
        setup: Class only. Setup method name.
        teardown: Class only. Teardown method name.
    """

    env: Env | None = None
    accel: str | None = None

    # lifecycle (class-only)
    entry: str | None = None
    setup: str | None = None
    teardown: str | None = None


def extract_metadata(decorator: ast.Call, is_class_def: bool) -> Metadata | None:
    """Extract Metadata from a single decorator AST node."""
    env = None
    accel = None
    entry = None
    setup = None
    teardown = None

    for keyword in decorator.keywords:
        if keyword.arg == "env":
            env = ast.literal_eval(keyword.value)
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
        if env is None and accel is None:
            return None
        else:
            return Metadata(env=env, accel=accel)
    if entry is None:
        raise ValueError("Class metadata must specify 'entry' method.")
    return Metadata(env=env, accel=accel, entry=entry, setup=setup, teardown=teardown)
