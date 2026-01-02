import ast
from single_spec.ast_utils import update_ast
from ast_eq import ast_eq


def test_update_ast():
    source = """
@required(env="python:3.10", gpu="2xA100")
@tool
@another_decorator(param=42)
def my_function():
    pass

print("done")

def another_function():
    pass
    """
    replacement = """
@tool
@another_decorator(param=42)
def my_function():
    print("This is the updated function.")
    """

    ast_node = ast.parse(source)
    updated = {"my_function": ast.parse(replacement).body[0]}
    updated_ast = update_ast(ast_node, updated)
    assert ast_eq(
        updated_ast,
        ast.parse("""@tool
@another_decorator(param=42)
def my_function():
    print("This is the updated function.")

print("done")

def another_function():
    pass"""),
    )
