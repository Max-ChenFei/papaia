import ast
from copy import deepcopy
from string import Template

from .util import extract_fields_and_call_args, get_docstring_stmt


def func2fastapi(fn: ast.FunctionDef) -> tuple[list[str], str, str]:
    """
    Return the pip install list, FastAPI server code (str), and the code template (str) to invoke the FastAPI endpoint for the given function AST node.
    """
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

    is_async = isinstance(fn, ast.AsyncFunctionDef)
    endpoint_def = "async def" if is_async else "def"
    call_prefix = "await " if is_async else ""

    pip_install = ["fastapi", "pydantic"]
    code = f'''import traceback

from fastapi import FastAPI, HTTPException
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
{endpoint_def} {fn_name}_endpoint(payload: {req_model}):
    try:
        result = {call_prefix}{fn_name}({", ".join(call_args)})
        return {resp_model}(result=result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={{"error": f"{{type(e).__name__}}: {{e}}", "traceback": traceback.format_exc()}})
'''

    # Build payload dict for the invoke template
    payload_items = ", ".join([f'"{arg.arg}": {arg.arg}' for arg in fn.args.args])

    invoke = deepcopy(fn)
    doc_stmt = get_docstring_stmt(invoke)

    new_body = ast.parse(f"""
from papaia.exec.code_gen.call_tool import call_tool
return call_tool({fn_name!r}, "$base_url{route}", {{{payload_items}}})""").body
    invoke.body = ([doc_stmt] if doc_stmt is not None else []) + new_body
    ast.fix_missing_locations(invoke)
    invoke_template = Template(ast.unparse(invoke))
    return (pip_install, code, invoke_template)
