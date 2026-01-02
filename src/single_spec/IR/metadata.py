import ast
from dataclasses import dataclass

from .env import Env


# Todo: capblitiess?
@dataclass(frozen=True)
class Metadata:
    env: Env | None = None  # runtime environment.
    gpu: int | None = None  # GPU requirement as a string (e.g., "2xA100").
    # lifecycle
    entry: str | None = None  # class only; method name
    setup: str | None = None  # class only; method name
    teardown: str | None = None  # class only; method name


def extract_metadata(decorator: ast.Call, is_class_def: bool) -> Metadata | None:
    """Extract Metadata from a single decorator AST node."""
    env = None
    gpu = None
    entry = None
    setup = None
    teardown = None

    for keyword in decorator.keywords:
        if keyword.arg == "env":
            env = ast.literal_eval(keyword.value)
        elif keyword.arg == "gpu":
            gpu = ast.literal_eval(keyword.value)
        elif is_class_def:
            if keyword.arg == "entry":
                entry = ast.literal_eval(keyword.value)
            elif keyword.arg == "setup":
                setup = ast.literal_eval(keyword.value)
            elif keyword.arg == "teardown":
                teardown = ast.literal_eval(keyword.value)

    if not is_class_def:
        if env is None and gpu is None:
            return None
        else:
            return Metadata(env=env, gpu=gpu)
    if entry is None:
        raise ValueError("Class metadata must specify 'entry' method.")
    return Metadata(env=env, gpu=gpu, entry=entry, setup=setup, teardown=teardown)
