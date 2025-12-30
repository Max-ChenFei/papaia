"""
In-memory registry populated at import time.
"""

from typing import Any
from .metadata import Metadata

RegistryEntry = tuple[Any, Metadata]

_REGISTRY: dict[str, RegistryEntry] = {}


def _default_key(obj: Any) -> str:
    return getattr(obj, "__qualname__", getattr(obj, "__name__", "<?>"))


def register(obj: Any, metadata: Metadata) -> None:
    """Register an object with a given name."""
    name = _default_key(obj)
    if name in _REGISTRY:
        raise ValueError(f"An object with name '{name}' is already registered.")
    _REGISTRY[name] = (obj, metadata)


def get_registered(name: str) -> RegistryEntry | None:
    """Retrieve a registered object by name."""
    return _REGISTRY.get(name)


def all_registered() -> dict[str, RegistryEntry]:
    """Get all registered objects."""
    return _REGISTRY


def clear_registry() -> None:
    """Clear the registry."""
    _REGISTRY.clear()
