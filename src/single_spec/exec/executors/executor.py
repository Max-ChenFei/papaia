import ast
from abc import ABC, abstractmethod

from ...IR import Desc


class Executor(ABC):
    def run(self, desc: Desc) -> str:
        code = self._generate_code(desc)
        return self._deploy(desc, code)

    @abstractmethod
    def stop(self, name: str) -> None:
        """Stop any running processes or clean up resources if needed."""
        raise NotImplementedError

    @abstractmethod
    def _generate_code(self, desc: Desc) -> ast.AST:
        """Generate runnable code/artifacts for this backend."""
        raise NotImplementedError

    @abstractmethod
    def _deploy(self, desc: Desc, generate_code: ast.AST) -> ast.AST:
        """Deploy artifact and return an access stub, make sure to keep the same signature."""
        raise NotImplementedError
