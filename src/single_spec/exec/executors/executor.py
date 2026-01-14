import ast
from string import Template
from abc import ABC, abstractmethod

from ..nodes import Node
from ...IR import Desc


class Executor(ABC):
    def run(self, desc: Desc, node: Node) -> ast.AST:
        code, invoke_template = self._generate_code(desc)
        return ast.parse(self._deploy(desc, code, invoke_template, node))

    @abstractmethod
    def stop(self, name: str) -> None:
        """Stop any running processes or clean up resources if needed."""
        raise NotImplementedError

    @abstractmethod
    def _generate_code(self, desc: Desc) -> tuple[str, str]:
        """Generate runnable code string."""
        raise NotImplementedError

    @abstractmethod
    def _deploy(
        self,
        desc: Desc,
        generate_code: str | None,
        invoke_template: Template,
        node: Node,
    ) -> str:
        """Deploy artifact and return an access stub, make sure to keep the same signature."""
        raise NotImplementedError
