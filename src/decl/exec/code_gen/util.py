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


def extract_fields_and_call_args(
    fn: ast.FunctionDef,
    is_class_method: bool = False,
) -> tuple[list[str], list[str], str, bool]:
    # Positional-or-keyword args (common case)
    args = fn.args.args

    # Skip 'self' or 'cls' for class methods
    if is_class_method and len(args) > 0:
        args = args[1:]

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
    return fields, call_args, ret, needs_any


def extract_method(cls: ast.ClassDef, name) -> ast.FunctionDef:
    method = None
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            method = node
            break
    if method is None:
        raise ValueError(f"No method named `{name}` found in class `{cls.name}`.")
    return method


def get_docstring_stmt(fn: ast.FunctionDef):
    """Return the docstring statement node if present, else None."""
    if not fn.body:
        return None
    first = fn.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return first
    return None
