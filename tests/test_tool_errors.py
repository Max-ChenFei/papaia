"""Errors of out-of-process tools name the tool and say what went wrong."""
import ast

import pytest

from papaia.exec.code_gen import func2fastapi
from papaia.exec.code_gen import call_tool as call_tool_module
from papaia.exec.code_gen.call_tool import ToolError, call_tool

TOOL = '''
def divide(a: int, b: int) -> float:
    return a / b
'''


@pytest.fixture
def service(monkeypatch):
    """Route the stub's HTTP calls to the generated service, in-process."""
    from fastapi.testclient import TestClient

    _, code, _ = func2fastapi(ast.parse(TOOL).body[0])
    ns: dict = {}
    exec(code, ns)
    client = TestClient(ns["app"])
    monkeypatch.setattr(
        call_tool_module.requests,
        "post",
        lambda url, json: client.post(url.removeprefix("http://svc"), json=json),
    )


def test_result_is_returned(service):
    assert call_tool("divide", "http://svc/divide", {"a": 6, "b": 3}) == 2.0


def test_tool_exception_names_tool_and_error(service, capsys):
    with pytest.raises(ToolError, match=r"Tool 'divide' failed in its service: ZeroDivisionError: division by zero") as e:
        call_tool("divide", "http://svc/divide", {"a": 1, "b": 0})
    assert "Traceback in the tool's service" in str(e.value) and "in divide" in str(e.value)
    assert "Traceback" in capsys.readouterr().err  # also printed by the service


def test_invalid_arguments_are_readable(service):
    with pytest.raises(ToolError, match=r"Tool 'divide': invalid arguments \(a: .*integer"):
        call_tool("divide", "http://svc/divide", {"a": "x", "b": 1})


def test_non_serializable_argument():
    with pytest.raises(ToolError, match=r"Tool 'divide': arguments must be JSON-serializable"):
        call_tool("divide", "http://127.0.0.1:9/divide", {"a": object(), "b": 1})


def test_unreachable_service():
    with pytest.raises(ToolError, match=r"Tool 'divide': its service at http://127.0.0.1:9/divide is not reachable"):
        call_tool("divide", "http://127.0.0.1:9/divide", {"a": 1, "b": 1})
