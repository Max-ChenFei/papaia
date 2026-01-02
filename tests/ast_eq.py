import ast


def ast_norm(t) -> str:
    return ast.dump(t, include_attributes=False)


def ast_eq(src1: ast.AST, src2: ast.AST) -> bool:
    return ast_norm(src1) == ast_norm(src2)
