import ast
from string import Template

from .executor import Executor
from ..code_gen import func2fastapi, cls2fastapi
from ...IR import Desc


class AnotherProcess(Executor):
    """
    execution in another execution environments (e.g., Docker, remote servers), not same as the CurrentProcess.
    """

    def stop(self, name: str) -> None:
        pass

    def _generate_code(self, desc: Desc) -> tuple[str, str]:
        if ast.isfunction(desc.ast_node):
            return func2fastapi(desc.ast_node)
        elif ast.isclass(desc.ast_node):
            return cls2fastapi(
                desc.ast_node,
                desc.metadata.entry,
                desc.metadata.setup,
                desc.metadata.teardown,
            )
        else:
            raise NotImplementedError(
                f"Unsupported AST node type: {type(desc.ast_node)}"
            )

    def _deploy(self, desc: Desc, generate_code: str, invoke_template: Template) -> str:
        raise NotImplementedError
