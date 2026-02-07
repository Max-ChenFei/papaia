import ast
from copy import deepcopy
from string import Template

from .util import extract_fields_and_call_args, extract_method, get_docstring_stmt


def cls2fastapi(
    cls: ast.AST,
    entry: str,
    setup: str | None = None,
    teardown: str | None = None,
) -> tuple[list[str], str, Template]:
    """
    Return the pip install list, FastAPI server code (str), and the code template (str) to invoke the FastAPI endpoint for the given function AST node.
    """
    cls_no_decorators = deepcopy(cls)
    cls_no_decorators.decorator_list = []  # remove decorators
    cls_no_decorators.bases = []  # remove the child inheritance
    cls_src = ast.unparse(cls_no_decorators)

    cls_name = cls.name
    route = f"/{cls_name.lower()}"
    entry_fn = extract_method(cls, entry)
    fields, call_args, ret, needs_any = extract_fields_and_call_args(
        entry_fn, is_class_method=True
    )
    imports_any = "from typing import Any\n" if needs_any else ""
    req_model = f"{cls_name.title().replace('_', '')}Request"
    resp_model = f"{cls_name.title().replace('_', '')}Response"

    setup_code = (
        ""
        if setup is None
        else f"""
@app.on_event("startup")
def startup_event():
    instance.{setup}()"""
    )

    teardown_code = (
        ""
        if teardown is None
        else f"""
@app.on_event("shutdown")
def shutdown_event():
    instance.{teardown}()"""
    )
    pip_install = ["fastapi", "pydantic"]
    code = f"""from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
{imports_any}
app = FastAPI()

# --- your class (kept as-is) ---
{cls_src}

instance = {cls_name}()
{setup_code}

{teardown_code}

# --- auto-generated schemas ---
class {req_model}(BaseModel):
{chr(10).join(fields) if fields else "    pass"}

class {resp_model}(BaseModel):
    result: {ret}

# --- auto-generated endpoint ---
@app.post("{route}", response_model={resp_model})
def {cls_name.lower()}_endpoint(payload: {req_model}):
    try:
        result = instance.{entry}({", ".join(call_args)})
        return {resp_model}(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""

    # Build payload dict for the invoke template
    payload_items = ", ".join(
        [f'"{arg.arg}": {arg.arg}' for arg in entry_fn.args.args[1:]]
    )

    invoke = deepcopy(entry_fn)
    doc_stmt = get_docstring_stmt(invoke)

    new_body = ast.parse(f"""
import requests
url = f"$base_url{route}"
payload = {{{payload_items}}}
response = requests.post(url, json=payload)
if response.status_code != 200:
    error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
    raise Exception(f"Server error ({{response.status_code}}): {{error_detail}}")
return response.json()["result"]""").body
    invoke.body = ([doc_stmt] if doc_stmt is not None else []) + new_body
    ast.fix_missing_locations(invoke)

    invoke_cls = deepcopy(cls)
    for i, node in enumerate(invoke_cls.body):
        if isinstance(node, ast.FunctionDef) and node.name == entry:
            invoke_cls.body[i] = invoke
            break

    invoke_template = Template(ast.unparse(invoke_cls))
    return (pip_install, code, invoke_template)
