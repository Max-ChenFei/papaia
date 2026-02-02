import ast
from string import Template

from .executor import Executor
from ...IR import Desc, Node
from ...accel_assign import assign_accel_devices_code


class CurrentProcess(Executor):
    def _generate_code(self, desc: Desc) -> tuple[list[str] | None, str | None, str]:
        """Return source code as-is since it runs in the same process."""
        devide_code = assign_accel_devices_code(
            desc.ast_node.name, desc.assigned_accel_devices
        )
        imports = "\n".join([ast.unparse(imp) for imp in desc.imports])
        code_body = ast.unparse(desc.ast_node)
        return (None, None, f"{devide_code}\n{imports}\n{code_body}")

    def _deploy(
        self,
        node: Node,
        desc: Desc,
        generate_code: str | None,
        invoke_template: Template,
    ) -> str:
        """No deployment needed for in-process execution. Return the original source code."""
        return invoke_template
