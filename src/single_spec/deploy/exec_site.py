from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecSite:
    name: str
    capabilities: dict[str, Any]
