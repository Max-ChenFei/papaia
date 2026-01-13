from abc import ABC, abstractmethod
import ast
from string import Template

from ...IR import Desc


class Executor(ABC):
    def run(self, desc: Desc) -> ast.AST:
        code, invoke_template = self._generate_code(desc)
        return ast.parse(self._deploy(desc, code, invoke_template))

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
        self, desc: Desc, generate_code: str | None, invoke_template: Template
    ) -> str:
        """Deploy artifact and return an access stub, make sure to keep the same signature."""
        raise NotImplementedError
