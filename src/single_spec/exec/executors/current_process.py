import ast
from string import Template

from .executor import Executor
from ..nodes import Node
from ...IR import Desc


class CurrentProcess(Executor):
    def stop(self, name: str) -> None:
        # no-op
        pass

    def _generate_code(self, desc: Desc) -> tuple[str | None, str]:
        """Return source code as-is since it runs in the same process."""
        return None, "\n".join(
            [ast.unparse(imp) for imp in desc.imports]
        ) + "\n" + ast.unparse(desc.ast_node)

    def _deploy(
        self,
        desc: Desc,
        generate_code: str | None,
        invoke_template: Template,
        node: Node,
    ) -> str:
        """No deployment needed for in-process execution. Return the original source code."""
        return invoke_template
