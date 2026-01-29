import ast
from string import Template
from abc import ABC, abstractmethod

from ...IR import Desc
from ...utils import merge
from ...accel_assign import assign_accel_devices_code


class Executor(ABC):
    _desc: dict[str, Desc] = {}

    def run(self, desc: Desc) -> ast.AST:
        self._desc[desc.ast_node.name] = desc

        code, invoke_template = self._generate_code(desc)
        if code is not None:
            if desc.imports:
                code = merge(ast.parse(code), desc.imports)
            code = f"{assign_accel_devices_code(desc.ast_node.name, desc.assigned_accel_devices)}\n{code}"
        return ast.parse(self._deploy(desc, code, invoke_template))

    def stop(self, name: str) -> None:
        """Stop any running processes or clean up resources if needed."""
        if name in self._desc:
            self._desc[name].assigned_node.release_accel_devices(
                self._desc[name].assigned_accel_devices
            )
            self._desc[name].assigned_node = None
            self._desc[name].assigned_accel_devices = None
            del self._desc[name]

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
