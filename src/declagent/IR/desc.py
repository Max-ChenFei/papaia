import ast
from dataclasses import dataclass

from .pip_install import PipInstall, merge_pip_install
from .resources import Resources
from .metadata import Metadata, extract_metadata
from ..decorators import decorator_keywords
from ..utils import (
    is_class_def,
    split_decorator,
    update_decorator_list,
)
from .nodes import Node


@dataclass
class Desc:
    ast_node: ast.AST
    metadata: Metadata
    imports: list[ast.Import | ast.ImportFrom] | None = None
    assigned_node: Node | None = None
    assigned_accel_devices: str | None = None

    @property
    def resources(self) -> Resources:
        return self.metadata.resources

    @property
    def pip_install(self) -> PipInstall | list[PipInstall] | None:
        return self.metadata.pip_install

    def append_pip_install(self, value: list[str] | None) -> None:
        self.metadata.pip_install = merge_pip_install(self.metadata.pip_install, value)


def extract_desc(mod: ast.Module) -> dict[str, Desc]:
    """Extract Desc from function and class definitions in the AST that are marked with our decorator."""
    found: dict[str, Desc] = {}
    imports = []
    for node in mod.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
            continue

        our_decorator, rest_decorators = split_decorator(node, decorator_keywords)
        if not our_decorator:
            continue

        metadata = extract_metadata(our_decorator, is_class_def(node))
        if metadata is None:
            continue

        new_node = update_decorator_list(node, rest_decorators)
        desc = Desc(imports=imports, ast_node=new_node, metadata=metadata)
        found[node.name] = desc
    return found
