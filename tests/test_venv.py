import requests
import ast

from single_spec.exec.executors.venv import Venv
from string import Template
from single_spec.IR import Desc, Metadata


def test_venv_executor_creation():
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
    venv_executor = Venv()
    invoke = venv_executor._deploy(
        desc=desc, generate_code=server_code, invoke_template=template
    )

    assert "base_url=http://localhost:" in invoke
    request_url = invoke.split("base_url=")[1] + "/add2"

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
