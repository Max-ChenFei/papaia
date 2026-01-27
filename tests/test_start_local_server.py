import requests
import subprocess
import ast
import os
from pathlib import Path

from single_spec.exec import available_nodes
from single_spec.IR import Desc, Metadata, Resources
from single_spec.exec.executors.local_docker import (
    start_fastapi_service,
    run_cmd,
    pick_free_port,
)


def test_run_cmd():
    host_port = 123456
    docker_image = "python:3.9-slim"
    mount_path = "app"
    host_port = pick_free_port()

    cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "-p",
        f"{host_port}:8000",
        "--name",
        f"svc_{host_port}",
        "-v",
        f"{mount_path}:/app",
        "-w",
        "/app",
        f"{docker_image}",
        "bash",
        "-lc",
        "ls -la /app && pip install fastapi uvicorn && uvicorn run:app --host 0.0.0.0 --port 8000",
    ]

    container_id = run_cmd(*cmd)
    p = subprocess.Popen(["docker", "logs", "-f", container_id], text=True)
    p.wait()
    assert container_id is not None


def test_start_local_server():
    original_dir = os.getcwd()
    code = '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# --- your function (kept as-is) ---
def add2(a: int, b: int = 1) -> int:
    """Adds two numbers.

    Args:
        a: First number.
        b: Second number. Defaults to 1.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b

# --- auto-generated schemas ---
class Add2Request(BaseModel):
    a: int
    b: int = 1

class Add2Response(BaseModel):
    result: int

# --- auto-generated endpoint ---
@app.post("/add2", response_model=Add2Response)
def add2_endpoint(payload: Add2Request):
    try:
        result = add2(payload.a, payload.b)
        return Add2Response(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))'''
    os.chdir(Path(__file__).parent)
    exec_nodes, local_index = available_nodes()
    node = exec_nodes[local_index]
    service = start_fastapi_service(
        code,
        Desc(
            ast.parse(code).body, Metadata(env="python:3.9-slim", resources=Resources())
        ),
        node,
    )
    response = requests.post(
        f"{service.base_url}/add2",
        json={"a": 3, "b": 4},
    )
    assert response.status_code == 200
    assert response.json().get("result") == 7, f"Unexpected response: {response.text}"

    service.stop()
    os.chdir(original_dir)


def test_start_local_server_extral_packages():
    original_dir = os.getcwd()
    code = '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# --- your function (kept as-is) ---
def add2(a: int, b: int = 1) -> int:
    """Adds two numbers.

    Args:
        a: First number.
        b: Second number. Defaults to 1.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b

# --- auto-generated schemas ---
class Add2Request(BaseModel):
    a: int
    b: int = 1

class Add2Response(BaseModel):
    result: int

# --- auto-generated endpoint ---
@app.post("/add2", response_model=Add2Response)
def add2_endpoint(payload: Add2Request):
    try:
        import numpy as np  # extra package test
        result = add2(payload.a, payload.b)
        return Add2Response(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))'''
    os.chdir(Path(__file__).parent)
    exec_nodes, local_index = available_nodes()
    node = exec_nodes[local_index]
    service = start_fastapi_service(
        code,
        Desc(
            ast.parse(code).body,
            Metadata(env=("python:3.9-slim", ["numpy"]), resources=Resources()),
        ),
        node,
    )
    response = requests.post(
        f"{service.base_url}/add2",
        json={"a": 3, "b": 4},
    )
    assert response.status_code == 200
    assert response.json().get("result") == 7, f"Unexpected response: {response.text}"

    service.stop()
    os.chdir(original_dir)


def test_start_local_server_fail():
    original_dir = os.getcwd()
    code = """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app2 = FastAPI()
"""
    try:
        os.chdir(Path(__file__).parent)
        exec_nodes, local_index = available_nodes()
        node = exec_nodes[local_index]
        service = start_fastapi_service(
            code,
            Desc(
                ast.parse(code).body,
                Metadata(env="python:3.9-slim", resources=Resources()),
            ),
            node,
        )
        service.stop()
        assert False, "Expected failure due to missing 'app' variable"
    except (RuntimeError, TimeoutError) as e:
        # Expected error - service should fail to start
        print(f"Expected error caught: {e}")
        assert (
            "app" in str(e).lower()
            or "timeout" in str(e).lower()
            or "failed" in str(e).lower()
        )
    except Exception as e:
        # Unexpected error
        raise AssertionError(f"Unexpected error type: {type(e).__name__}: {e}")
    finally:
        os.chdir(original_dir)
