import ast
from string import Template

from ...IR import Desc
from .executor import Executor


class CurrentProcess(Executor):
    def stop(self, name: str) -> None:
        # no-op
        pass

    def _generate_code(self, desc: Desc) -> tuple[str | None, str]:
        """Return source code as-is since it runs in the same process."""
        return None, ast.unparse(desc.ast_node)

    def _deploy(
        self, desc: Desc, generate_code: str | None, invoke_template: Template
    ) -> str:
        """No deployment needed for in-process execution. Return the original source code."""
        return invoke_template
