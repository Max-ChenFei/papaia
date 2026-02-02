import ast
import asyncio
from string import Template
from abc import ABC, abstractmethod

from ...IR import Desc, Node
from ...utils import merge
from ...accel_assign import assign_accel_devices_code


class Executor(ABC):
    _desc: dict[str, Desc] = {}

    async def run(self, node: Node, desc: Desc) -> ast.AST:
        self._desc[desc.ast_node.name] = desc

        pip_install, code, invoke_template = self._generate_code(desc)
        desc.append_pip_install(pip_install)
        if code is not None:
            if desc.imports:
                code = merge(ast.parse(code), desc.imports)
            code = f"{assign_accel_devices_code(desc.ast_node.name, desc.assigned_accel_devices)}\n{code}"
        deploy_result = await asyncio.to_thread(
            self._deploy, node, desc, code, invoke_template
        )
        return ast.parse(deploy_result)

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
    def _generate_code(self, desc: Desc) -> tuple[list[str] | None, str | None, str]:
        """Generate runnable code string."""
        raise NotImplementedError

    @abstractmethod
    def _deploy(
        self,
        node: Node,
        desc: Desc,
        generate_code: str | None,
        invoke_template: Template,
    ) -> str:
        """Deploy artifact and return an access stub, make sure to keep the same signature."""
        raise NotImplementedError
