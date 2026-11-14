"""Unsupported tool definitions fail early with a clear message."""
import ast
import os
import sys
import tempfile
from pathlib import Path

import pytest

from papaia import compile_and_run
from papaia.IR import extract_desc
from papaia.exec.code_gen import func2fastapi

TESTS_DIR = Path(__file__).parent


def _run(src: str, extra_files: dict[str, str] = {}):
    original_dir = os.getcwd()
    os.chdir(TESTS_DIR)  # exec_nodes.toml
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            for name, text in extra_files.items():
                (Path(tmpdir) / name).write_text(text)
            sys.path.insert(0, tmpdir)
            try:
                main = Path(tmpdir) / "agent.py"
                main.write_text(src)
                compile_and_run(main)
            finally:
                sys.path.remove(tmpdir)
                for name in extra_files:
                    sys.modules.pop(Path(name).stem, None)
    finally:
        os.chdir(original_dir)


def test_imported_tool_is_rejected():
    tools = '''from papaia import required_fn

@required_fn(accel="A100:1")
def grounding(url: str) -> str:
    return url
'''
    with pytest.raises(RuntimeError, match="'grounding'.*not compiled"):
        _run("from my_tools import grounding\nprint(grounding('x'))\n",
             {"my_tools.py": tools})


def test_nested_tool_is_rejected():
    src = '''from papaia import required_fn

def make():
    @required_fn(cpus=1)
    def inner(x: int) -> int:
        return x
    return inner

make()
'''
    with pytest.raises(RuntimeError, match="inner.*not compiled"):
        _run(src)


def test_plain_python_run_still_works():
    # Without `papaia run`, decorators are no-ops.
    from papaia import required_fn

    @required_fn(accel="A100:1")
    def f(x: int) -> int:
        return x

    assert f(1) == 1


def test_non_literal_decorator_argument():
    src = '''GPU = "A100:1"

@required_fn(accel=GPU)
def grounding(url: str) -> str:
    return url
'''
    with pytest.raises(ValueError, match="Tool 'grounding'.*'accel' must be a literal"):
        extract_desc(ast.parse(src))


@pytest.mark.parametrize("params", ["*args", "**kw", "x, *, y", "x, /"])
def test_unsupported_parameters_out_of_process(params):
    fn = ast.parse(f"def tool({params}):\n    pass\n").body[0]
    with pytest.raises(ValueError, match="Tool 'tool'.*unsupported"):
        func2fastapi(fn)


@pytest.mark.parametrize("src", [
    "from papaia import required_fn as rf\n\n@rf(cpus=1)\ndef tool(x: int) -> int:\n    return x\n",
    "import papaia\n\n@papaia.required_fn(cpus=1)\ndef tool(x: int) -> int:\n    return x\n",
    "import papaia as p\n\n@p.required_fn(cpus=1)\ndef tool(x: int) -> int:\n    return x\n",
    "from papaia import required_fn\n\n@required_fn()\ndef tool(x: int) -> int:\n    return x\n",
])
def test_decorator_forms_are_compiled(src):
    desc = extract_desc(ast.parse(src))
    assert list(desc) == ["tool"]
    assert desc["tool"].ast_node.decorator_list == []


def test_positional_decorator_arguments_rejected():
    src = "@required_fn(['requests'])\ndef tool(x: int) -> int:\n    return x\n"
    with pytest.raises(ValueError, match="Tool 'tool'.*by keyword"):
        extract_desc(ast.parse(src))


def test_unsupported_parameters_rejected_for_every_tool():
    # Checked at compile time for in-process tools too, so the tool stays movable.
    src = "@required_fn(cpus=1)\ndef tool(*args):\n    pass\n"
    with pytest.raises(ValueError, match="Tool 'tool'.*unsupported: \\*args"):
        extract_desc(ast.parse(src))
    src = ('@required_cls(entry="run")\nclass Tool:\n'
           '    def run(self, x, *, y):\n        pass\n')
    with pytest.raises(ValueError, match="Tool 'Tool'.*unsupported: y"):
        extract_desc(ast.parse(src))


def test_async_tool_endpoint_awaits():
    from fastapi.testclient import TestClient

    fn = ast.parse("async def tool(x: int) -> int:\n    return x + 1\n").body[0]
    _, code, _ = func2fastapi(fn)
    ns: dict = {}
    exec(code, ns)
    resp = TestClient(ns["app"]).post("/tool", json={"x": 1})
    assert resp.status_code == 200 and resp.json() == {"result": 2}
