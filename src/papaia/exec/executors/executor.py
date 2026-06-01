import ast
import asyncio
from abc import ABC, abstractmethod

from ...IR import Desc, Node


class Executor(ABC):
    _desc: dict[str, Desc] = {}

    async def run(self, node: Node, desc: Desc) -> ast.AST:
        self._desc[desc.ast_node.name] = desc

        pip_install, code, invoke_template = self._generate_code(desc)
        desc.append_pip_install(pip_install)

        url = await asyncio.to_thread(self._deploy, node, desc, code)
        access_stub = (
            invoke_template.substitute(base_url=url) if url else invoke_template
        )
        return ast.parse(access_stub)

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
    def _deploy(self, node: Node, desc: Desc, generate_code: str) -> str:
        """Deploy artifact and return an access stub, make sure to keep the same signature."""
        raise NotImplementedError
