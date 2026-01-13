import ast

from .util import extract_fields_and_call_args


def func2fastapi(mod: ast.AST) -> str:
    """Generate a FastAPI app template for the given function ast node."""
    func_src = ast.unparse(mod)
    fn = next((n for n in mod.body if isinstance(n, ast.FunctionDef)), None)
    if fn is None:
        raise ValueError("No top-level `def ...` found in the provided string.")

    fn_name = fn.name
    route = f"/{fn_name}"
    fields, call_args, ret, needs_any = extract_fields_and_call_args(fn)
    imports_any = "from typing import Any\n" if needs_any else ""
    req_model = f"{fn_name.title().replace('_', '')}Request"
    resp_model = f"{fn_name.title().replace('_', '')}Response"

    code = f'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
{imports_any}
app = FastAPI()

# --- your function (kept as-is) ---
{func_src.strip()}

# --- auto-generated schemas ---
class {req_model}(BaseModel):
{chr(10).join(fields) if fields else "    pass"}

class {resp_model}(BaseModel):
    result: {ret}

# --- auto-generated endpoint ---
@app.post("{route}", response_model={resp_model})
def {fn_name}_endpoint(payload: {req_model}):
    try:
        result = {fn_name}({", ".join(call_args)})
        return {resp_model}(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
'''
    return code
