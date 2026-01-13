import ast


def _ann_to_str(node: ast.AST | None) -> str:
    if node is None:
        return "Any"
    # Python 3.9+:
    return ast.unparse(node)


def _literal_default(node: ast.AST | None):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None  # non-literal default (e.g., function call)


def func2fastapi(mod: ast.AST, route: str | None = None) -> str:
    """Generate a FastAPI app template for the given function ast node."""
    func_src = ast.unparse(mod)
    fn = next((n for n in mod.body if isinstance(n, ast.FunctionDef)), None)
    if fn is None:
        raise ValueError("No top-level `def ...` found in the provided string.")

    fn_name = fn.name
    route = route or f"/{fn_name}"

    # Positional-or-keyword args (common case)
    args = fn.args.args
    defaults = fn.args.defaults
    # Align defaults with the last N args
    default_map = (
        {
            args[i].arg: defaults[i - (len(args) - len(defaults))]
            for i in range(len(args) - len(defaults), len(args))
        }
        if defaults
        else {}
    )

    fields = []
    call_args = []
    needs_any = False

    for a in args:
        name = a.arg
        typ = _ann_to_str(a.annotation)
        if typ == "Any":
            needs_any = True

        dnode = default_map.get(name)
        dval = _literal_default(dnode)

        if dnode is None:
            # required
            fields.append(f"    {name}: {typ}")
        elif dval is not None:
            # literal default => can embed safely
            fields.append(f"    {name}: {typ} = {repr(dval)}")
        else:
            # non-literal default; keep required, but comment it
            fields.append(f"    {name}: {typ}  # default is non-literal in source")

        call_args.append(f"payload.{name}")

    ret = _ann_to_str(fn.returns)
    if ret == "Any":
        needs_any = True

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
