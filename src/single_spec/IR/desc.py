import ast
from dataclasses import dataclass

from .metadata import Metadata, extract_metadata
from ..decorators import decorator_keywords
from ..ast_utils import is_class_def, split_decorator, update_decorator_list


@dataclass
class Desc:
    ast_node: ast.AST
    metadata: Metadata

    def resources(self) -> Metadata:
        return self.metadata.resources


def extract_desc(ast: ast.Module) -> dict[str, Desc]:
    """Extract Desc from function and class definitions in the AST that are marked with our decorator."""
    found: dict[str, Desc] = {}
    for node in ast.body:
        our_decorator, rest_decorators = split_decorator(node, decorator_keywords)
        if not our_decorator:
            continue

        metadata = extract_metadata(our_decorator, is_class_def(node))
        if metadata is None:
            continue

        new_node = update_decorator_list(node, rest_decorators)
        desc = Desc(ast_node=new_node, metadata=metadata)
        found[node.name] = desc
    return found
