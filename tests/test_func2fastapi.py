import ast
from single_spec.exec.code_gen import func2fastapi


def test_func2fastapi():
    src = """
def add2(a: int, b: int = 1) -> int:
    return a + b
    """

    code = func2fastapi(ast.parse(src))
    print(code)
    assert (
        code
        == """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# --- your function (kept as-is) ---
def add2(a: int, b: int=1) -> int:
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
        raise HTTPException(status_code=400, detail=str(e))
"""
    )
    assert code is not None
