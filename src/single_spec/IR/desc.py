import ast
from dataclasses import dataclass

from .env import Env
from .resources import Resources
from .metadata import Metadata, extract_metadata
from ..decorators import decorator_keywords
from ..utils import (
    is_class_def,
    split_decorator,
    update_decorator_list,
)


@dataclass
class Desc:
    imports: list[str] | None
    ast_node: ast.AST
    metadata: Metadata

    @property
    def resources(self) -> Resources:
        return self.metadata.resources

    @property
    def env(self) -> Env | None:
        return self.metadata.env


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
