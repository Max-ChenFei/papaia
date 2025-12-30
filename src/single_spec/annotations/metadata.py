from dataclasses import dataclass

from .runtime_env import Env


@dataclass(frozen=True)
class Metadata:
    env: Env | None = None  # runtime environment.
    gpu: int | None = None  # GPU requirement as a string (e.g., "2xA100").
    # lifecycle
    entry: str  # fn: function name; cls: method name
    setup: str = "__init__"  # class only; ignored for functions
    teardown: str | None = None  # class only; ignored for functions

    def __repr__(self):
        return (
            f"Metadata(env={self.env}, gpu={self.gpu}, "
            f"entry='{self.entry}', setup='{self.setup}', teardown='{self.teardown}')"
        )
