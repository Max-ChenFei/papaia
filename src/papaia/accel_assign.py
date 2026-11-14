import os

PREFIX = "TOOL_ACCEL_INDEXES__"
# use env not global variable for shared state across processes

def assign_accel_devices_code(name: str, indexes: str | None) -> None:
    """Assign accelerator indexes as a raw string like '0,1' to env."""
    if name == "":
        raise ValueError("Tool name cannot be empty")
    if indexes is None:
        return ""
    return f"""import os
os.environ["{PREFIX}{name}"] = "{indexes}"
"""


def assigned_accel_devices(name: str) -> str | None:
    """Return assigned accelerator indexes as a raw string like '0,1' from env."""
    if name == "":
        raise ValueError("Tool name cannot be empty")
    return os.environ.get(f"{PREFIX}{name}")


def assigned_device(name: str, default: str = "cpu") -> str:
    """Return a framework device string for a tool, e.g. ``"cuda:1"``, or ``default``.

    Uses the first accelerator assigned to the tool, so tool code stays the same
    whether the tool is placed on a node with accelerators or without them.
    """
    indexes = assigned_accel_devices(name)
    if not indexes:
        return default
    return f"cuda:{indexes.split(',')[0].strip()}"
