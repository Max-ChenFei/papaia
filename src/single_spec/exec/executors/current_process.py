import ast

from ...IR import Desc
from .executor import Executor


class CurrentProcess(Executor):
    def stop(self, name: str) -> None:
        # no-op
        pass

    def _generate_code(self, desc: Desc) -> ast.AST:
        """Return source code as-is since it runs in the same process."""
        return desc.ast_node

    def _deploy(self, desc: Desc, generate_code: ast.AST) -> ast.AST:
        """No deployment needed for in-process execution. Return the original source code."""
        return generate_code
