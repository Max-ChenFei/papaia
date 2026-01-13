import ast
from single_spec.exec.code_gen import func2fastapi, cls2fastapi

from ast_eq import ast_eq


def test_func2fastapi():
    src = """
def add2(a: int, b: int = 1) -> int:
    return a + b
    """

    code = func2fastapi(ast.parse(src))
    assert ast_eq(
        ast.parse(code),
        ast.parse("""from fastapi import FastAPI, HTTPException
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
"""),
    )
    assert code is not None


def test_cls2fastapi():
    src = """
class Adder:

    def add2(self, a: int, b: int = 1) -> int:
        return a + b
    
    def setup(self):
        print("setup called")
    
    def teardown(self):
        print("teardown called")
    """
    code = cls2fastapi(ast.parse(src), entry="add2", setup="setup", teardown="teardown")

    assert ast_eq(
        ast.parse(code),
        ast.parse("""from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app = FastAPI()
# --- your class (kept as-is) ---
class Adder:

    def add2(self, a: int, b: int=1) -> int:
        return a + b

    def setup(self):
        print('setup called')

    def teardown(self):
        print('teardown called')

instance = Adder()
@app.on_event("startup")
def startup_event():
    instance.setup()

@app.on_event("shutdown")
def shutdown_event():
    instance.teardown()

# --- auto-generated schemas ---
class AdderRequest(BaseModel):
    a: int
    b: int = 1

class AdderResponse(BaseModel):
    result: int

# --- auto-generated endpoint ---
@app.post("/adder", response_model=AdderResponse)
def adder_endpoint(payload: AdderRequest):
    try:
        result = instance.add2(payload.a, payload.b)
        return AdderResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""),
    )
