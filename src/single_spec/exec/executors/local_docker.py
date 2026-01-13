import ast

from ...IR import Desc
from .another_process import AnotherProcess


class LocalDocker(AnotherProcess):
    """
    Adapter for execution in local Docker containers.
    """

    def stop(self, name: str) -> None:
        pass

    def _generate_code(self, desc: Desc) -> ast.AST:
        raise NotImplementedError

    def _deploy(self, desc: Desc, generate_code: ast.AST) -> ast.AST:
        raise NotImplementedError
