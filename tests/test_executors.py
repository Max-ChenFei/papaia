import ast
import requests
from string import Template

from decl.exec.executors.venv import VenvExecutor
from decl.exec.executors.another_process import split_pip_install
from decl.IR import Desc, Metadata


def test_venv_executor():
    code = '''def add2(a: int, b: int = 1) -> int:
    """Adds two numbers.

    Args:
        a: First number.
        b: Second number. Defaults to 1.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b
'''

    server_code = f"""from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# --- your function (kept as-is) ---
{code.strip()}

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
        raise HTTPException(status_code=400, detail=str(e))"""

    template = Template("""base_url=$base_url""")
    desc = Desc(
        ast_node=ast.parse(code).body[0],
        metadata=Metadata(pip_install=(["fastapi", "uvicorn", "pydantic"])),
    )
    venv_executor = VenvExecutor()
    base_url = venv_executor._deploy(node=None, desc=desc, generate_code=server_code)

    invoke = template.substitute(base_url=base_url)
    assert "base_url=http://localhost:" in invoke
    request_url = base_url + "/add2"

    response = requests.post(
        request_url,
        json={"a": 5, "b": 7},
    )
    assert response.status_code == 200
    assert response.json().get("result") == 12, f"Unexpected response: {response.text}"

    venv_executor.stop(desc.ast_node.name)

    # After stopping, the server should not respond
    try:
        requests.post(
            request_url,
            json={"a": 5, "b": 7},
            timeout=1,
        )
        assert False, "Service should be stopped but is still running"
    except requests.exceptions.ConnectionError:
        # Expected - server is stopped
        pass


def test_write_requirements_file(tmp_path):
    reqs = ["fastapi==0.70.0", "uvicorn>=0.15.0", "pydantic"]
    req_file, _ = split_pip_install(tmp_path, reqs)

    with open(req_file, "r") as f:
        content = f.read().strip().split("\n")

    assert content == reqs


def test_write_requirements_file_from_path(tmp_path):
    src_req_file = tmp_path / "requirements.txt"
    reqs = ["fastapi==0.70.0", "uvicorn>=0.15.0", "pydantic"]
    with open(src_req_file, "w") as f:
        f.write("\n".join(reqs))

    req_file, _ = split_pip_install(tmp_path, str(src_req_file))

    with open(req_file, "r") as f:
        content = f.read().strip().split("\n")

    assert content == reqs


def test_write_requirements_file_FileNotFoundError(tmp_path):
    try:
        split_pip_install(tmp_path, "non_existent_requirements.txt")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass  # Expected exception
