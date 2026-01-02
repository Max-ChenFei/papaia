import ast

from single_spec.IR.desc import split_decorator, extract_desc
from single_spec.IR.metadata import extract_metadata

from ast_eq import ast_eq


def test_extract_fn_metadata():
    source = """
@required(env="python:3.10", gpu="2xA100")
def my_function():
    pass

print("done")
    """
    decorator = ast.parse(source).body[0].decorator_list[0]
    metadata = extract_metadata(decorator, is_class_def=False)
    assert metadata is not None
    assert metadata.env == "python:3.10"
    assert metadata.gpu == "2xA100"


def test_split_decorator():
    source = """
@required(env="python:3.10", gpu="2xA100")
@tool
@another_decorator(param=42)
def my_function():
    pass
    """
    ast_node = ast.parse(source).body[0]
    dec, rest_dec = split_decorator(ast_node, {"required"})
    assert ast_eq(dec, ast_node.decorator_list[0])
    assert [ast_eq(d1, d2) for d1, d2 in zip(rest_dec, ast_node.decorator_list[1:])]


def test_extract_desc_from_def():
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
    ast_node = ast.parse(source)
    descs = extract_desc(ast_node)
    assert "my_function" in descs
    assert "another_function" not in descs

    assert len(descs) == 1
    desc = descs["my_function"]
    assert ast_eq(
        desc.ast_node,
        ast.parse("""@tool
@another_decorator(param=42)
def my_function():
    pass""").body[0],
    )
    assert desc.metadata.env == "python:3.10"
    assert desc.metadata.gpu == "2xA100"


def test_extract_desc_from_def_cls():
    source = """
@required_cls(env="python:3.10", gpu="2xA100", entry="main_method")
@tool
@another_decorator(param=42)
class MyClass:
    def main_method(self):
        pass

print("done")

def another_function():
    pass
    """
    ast_node = ast.parse(source)
    descs = extract_desc(ast_node)
    assert "MyClass" in descs
    assert "another_function" not in descs

    assert len(descs) == 1
    desc = descs["MyClass"]
    assert ast_eq(
        desc.ast_node,
        ast.parse("""@tool
@another_decorator(param=42)
class MyClass:
    def main_method(self):
        pass""").body[0],
    )
    assert desc.metadata.env == "python:3.10"
    assert desc.metadata.gpu == "2xA100"
