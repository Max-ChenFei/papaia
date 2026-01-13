import ast

from .util import extract_fields_and_call_args, extract_method


def cls2fastapi(
    mod: ast.AST,
    entry: str,
    setup: str | None = None,
    teardown: str | None = None,
) -> str:
    """Generate a FastAPI app template for the given class ast node."""
    cls_src = ast.unparse(mod)
    cls = next((n for n in mod.body if isinstance(n, ast.ClassDef)), None)
    if cls is None:
        raise ValueError("No top-level `class ...` found in the provided string.")

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

    code = f'''from fastapi import FastAPI, HTTPException
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
'''
    return code
