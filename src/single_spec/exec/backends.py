from abc import ABC, abstractmethod
import ast

from ..IR import Desc


class ExecutionBackend(ABC):
    def run(self, desc: Desc) -> str:
        code = self._generate_code(desc)
        return self._deploy(desc, code)

    @abstractmethod
    def stop(self, name: str) -> None:
        """Stop any running processes or clean up resources if needed."""
        pass

    @abstractmethod
    def _generate_code(self, desc: Desc) -> ast.AST:
        """Generate runnable code/artifacts for this backend."""
        raise NotImplementedError

    @abstractmethod
    def _deploy(self, desc: Desc, generate_code: ast.AST) -> ast.AST:
        """Deploy artifact and return an access stub, make sure to keep the same signature."""
        raise NotImplementedError


class InProcessBackend(ExecutionBackend):
    def stop(self, name: str) -> None:
        # no-op
        pass

    def _generate_code(self, desc: Desc) -> ast.AST:
        """Return source code as-is since it runs in the same process."""
        return desc.ast_node

    def _deploy(self, desc: Desc, generate_code: ast.AST) -> ast.AST:
        """No deployment needed for in-process execution. Return the original source code."""
        return generate_code


class IsolatedAdapter(ExecutionBackend):
    """
    Adapter for execution in isolated environments (e.g., Docker, remote servers).
    """

    def stop(self, name: str) -> None:
        pass

    def _generate_code(self, desc: Desc) -> ast.AST:
        # Todo: implement code generation for isolated execution like http request
        pass

    def _deploy(self, desc: Desc, generate_code: ast.AST) -> ast.AST:
        pass


available_backends = {
    "local": InProcessBackend(),
    "isolated": IsolatedAdapter(),
}


def get_backend_by_name(name: str) -> ExecutionBackend:
    backend = available_backends.get(name)
    if backend is None:
        raise ValueError(f"Backend '{name}' is not available.")
    return backend


def add_backend(name: str, backend: ExecutionBackend) -> None:
    if name in available_backends:
        raise ValueError(f"Backend '{name}' already exists.")
    available_backends[name] = backend
