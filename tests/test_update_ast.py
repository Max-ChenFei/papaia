import ast

from ast_eq import ast_eq
from papaia.utils import update_ast


def test_update_ast():
    source = """
@required(pip_install="path/requirements.txt", accel="A100:2")
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
