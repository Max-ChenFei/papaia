import ast

from ...IR import Desc
from .executor import Executor


class AnotherProcess(Executor):
    """
    execution in another execution environments (e.g., Docker, remote servers), not same as the CurrentProcess.
    """

    def stop(self, name: str) -> None:
        pass

    def _generate_code(self, desc: Desc) -> ast.AST:
        # Todo: implement code generation for isolated execution like http request
        raise NotImplementedError

    def _deploy(self, desc: Desc, generate_code: ast.AST) -> ast.AST:
        raise NotImplementedError
