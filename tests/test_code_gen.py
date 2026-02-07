import ast

from ast_eq import ast_eq
from single_spec.exec.code_gen import func2fastapi, cls2fastapi


def test_func2fastapi():
    src = '''
def add2(a: int, b: int = 1) -> int:
    """Adds two numbers.

    Args:
        a: First number.
        b: Second number. Defaults to 1.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b
    '''

    pip_install, code, invoke_template = func2fastapi(ast.parse(src).body[0])

    assert ast_eq(
        ast.parse(code),
        ast.parse('''from fastapi import FastAPI, HTTPException
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
        raise HTTPException(status_code=400, detail=str(e))
'''),
    )

    assert (
        invoke_template.template
        == '''def add2(a: int, b: int=1) -> int:
    """Adds two numbers.

    Args:
        a: First number.
        b: Second number. Defaults to 1.

    Returns:
        The sum of ``a`` and ``b``.
    """
    import requests
    url = f'$base_url/add2'
    payload = {'a': a, 'b': b}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        error_detail = response.json().get('detail', response.text) if response.headers.get('content-type') == 'application/json' else response.text
        raise Exception(f'Server error ({response.status_code}): {error_detail}')
    return response.json()['result']'''
    )
    assert pip_install == ["fastapi", "pydantic"]


def test_cls2fastapi():
    src = '''class Adder(BaseTool):

    def add2(self, a: int, b: int = 1) -> int:
        """Adds two numbers.

        Args:
            a: First number.
            b: Second number. Defaults to 1.

        Returns:
            The sum of ``a`` and ``b``.
        """
        return a + b
    
    def setup(self):
        print("setup called")
    
    def teardown(self):
        print("teardown called")
    '''
    pip_install, code, invoke_template = cls2fastapi(
        ast.parse(src).body[0], entry="add2", setup="setup", teardown="teardown"
    )
    assert ast_eq(
        ast.parse(code),
        ast.parse('''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app = FastAPI()
# --- your class (kept as-is) ---
class Adder:

    def add2(self, a: int, b: int=1) -> int:
        """Adds two numbers.

        Args:
            a: First number.
            b: Second number. Defaults to 1.

        Returns:
            The sum of ``a`` and ``b``.
        """
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
'''),
    )
    assert ast_eq(
        ast.parse(invoke_template.template),
        ast.parse('''
class Adder(BaseTool):

    def add2(self, a: int, b: int = 1) -> int:
        """Adds two numbers.

        Args:
            a: First number.
            b: Second number. Defaults to 1.

        Returns:
            The sum of ``a`` and ``b``.
        """
        import requests
        url = f'$base_url/adder'
        payload = {'a': a, 'b': b}
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            error_detail = response.json().get('detail', response.text) if response.headers.get('content-type') == 'application/json' else response.text
            raise Exception(f'Server error ({response.status_code}): {error_detail}')
        return response.json()['result']
    
    def setup(self):
        print('setup called')
    
    def teardown(self):
        print('teardown called')
    '''),
    )
    assert pip_install == ["fastapi", "pydantic"]
