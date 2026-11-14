import ast
import copy
import tempfile
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Optional


def is_class_def(node: ast.AST) -> bool:
    return isinstance(node, ast.ClassDef)


def split_decorator(
    node: ast.AST,
    decorator_keywords: set[str],
    module_names: set[str] = frozenset(),
    attr_names: set[str] = frozenset(),
) -> tuple[Optional[ast.Call], list[ast.expr]]:
    """Split out our decorator from the decorator list of a function or class definition node.

    Matches ``@name(...)`` with ``name`` in ``decorator_keywords`` (including
    import aliases) and ``@mod.attr(...)`` with ``mod`` in ``module_names`` and
    ``attr`` in ``attr_names``.
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return None, []

    for i, dec in enumerate(node.decorator_list):
        if not isinstance(dec, ast.Call):
            continue
        f = dec.func
        is_ours = (isinstance(f, ast.Name) and f.id in decorator_keywords) or (
            isinstance(f, ast.Attribute)
            and isinstance(f.value, ast.Name)
            and f.value.id in module_names
            and f.attr in attr_names
        )
        if is_ours:
            rest_decorators = [d for j, d in enumerate(node.decorator_list) if j != i]
            return dec, rest_decorators

    return None, []


def check_tool_params(fn: ast.FunctionDef, tool_name: str) -> None:
    """Tool parameters must be positional-or-keyword so that the tool can run
    out of process (arguments are sent as a JSON object)."""
    unsupported = [a.arg for a in fn.args.posonlyargs + fn.args.kwonlyargs]
    unsupported += [f"*{a.arg}" for a in (fn.args.vararg,) if a]
    unsupported += [f"**{a.arg}" for a in (fn.args.kwarg,) if a]
    if unsupported:
        raise ValueError(
            f"Tool '{tool_name}' may only use positional-or-keyword parameters, "
            "so that it can run out of process; unsupported: "
            + ", ".join(unsupported)
        )


def update_decorator_list(
    node: ast.AST,
    decorator_list: list[ast.expr],
) -> ast.AST:
    node_copy = copy.deepcopy(node)
    node_copy.decorator_list = decorator_list
    return node_copy


def update_ast(
    mod: ast.Module,
    updated: dict[str, ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef],
) -> ast.Module:
    """Update the AST with the provided updated nodes for functions/classes."""
    for i, stmt in enumerate(mod.body):
        if (
            isinstance(stmt, ast.FunctionDef)
            or isinstance(stmt, ast.ClassDef)
            or isinstance(stmt, ast.AsyncFunctionDef)
        ):
            if stmt.name in updated:
                repl = ast.copy_location(updated[stmt.name], stmt)
                mod.body[i] = repl

    return mod


def read_ast(file_path: Path) -> ast.Module:
    src = file_path.read_text(encoding="utf-8")
    mod = ast.parse(src)
    return mod


def write_ast(mod: ast.Module, file_path: Path):
    new_src = ast.unparse(mod)
    file_path.write_text(new_src, encoding="utf-8")


def delete_file(file_path: Path):
    if file_path.exists():
        file_path.unlink()


def ruff_fix(file_path: Path):
    # Try to find ruff in the current environment or PATH
    ruff_cmd = shutil.which("ruff")

    # If not found in PATH, try the venv Scripts directory (Windows) or bin (Unix)
    if not ruff_cmd:
        venv_path = Path(sys.executable).parent
        potential_paths = [
            venv_path / "ruff.exe",  # Windows
            venv_path / "ruff",  # Unix-like
        ]
        for path in potential_paths:
            if path.exists():
                ruff_cmd = str(path)
                break

    # If still not found, silently skip (ruff is optional for fixing)
    if not ruff_cmd:
        return

    subprocess.run(
        [ruff_cmd, "check", str(file_path), "--fix"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def read_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def merge(node: ast.AST, all_imports: list[ast.stmt]) -> str:
    """merge the code and remove unused imports and return the merged code in a string."""
    mod = ast.Module(body=all_imports + [node], type_ignores=[])
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "temp.py"
        write_ast(mod, file_path)
        # Let ruff remove unused imports
        ruff_fix(file_path)
        return read_file(file_path)
