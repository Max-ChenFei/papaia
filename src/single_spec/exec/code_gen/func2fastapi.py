import ast
from copy import deepcopy
from string import Template

from .util import extract_fields_and_call_args, get_docstring_stmt


def func2fastapi(fn: ast.FunctionDef) -> tuple[list[str], str, str]:
    """Generate a FastAPI app template for the given function ast node and return the code template to invoke it."""
    # Use a copy of the function without decorators when generating the FastAPI code
    fn_no_decorators = deepcopy(fn)
    fn_no_decorators.decorator_list = []
    func_src = ast.unparse(fn_no_decorators)

    fn_name = fn.name
    route = f"/{fn_name}"
    fields, call_args, ret, needs_any = extract_fields_and_call_args(fn)
    imports_any = "from typing import Any\n" if needs_any else ""
    req_model = f"{fn_name.title().replace('_', '')}Request"
    resp_model = f"{fn_name.title().replace('_', '')}Response"

    pip_install = ["fastapi", "pydantic"]
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

    # Build payload dict for the invoke template
    payload_items = ", ".join([f'"{arg.arg}": {arg.arg}' for arg in fn.args.args])

    invoke = deepcopy(fn)
    doc_stmt = get_docstring_stmt(invoke)

    new_body = ast.parse(f"""
import requests
url = f"$base_url/{route}"
payload = {{{payload_items}}}
response = requests.post(url, json=payload)
response.raise_for_status()
return response.json()["result"]""").body
    invoke.body = ([doc_stmt] if doc_stmt is not None else []) + new_body
    ast.fix_missing_locations(invoke)
    invoke_template = Template(ast.unparse(invoke))
    return (pip_install, code, invoke_template)
