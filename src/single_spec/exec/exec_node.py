from dataclasses import dataclass

from ..IR.resources import Resources


@dataclass(frozen=True)
class ExecNode:
    name: str
    resources: Resources
