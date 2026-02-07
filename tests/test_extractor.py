import ast

from ast_eq import ast_eq
from declagent.IR.desc import split_decorator, extract_desc
from declagent.IR.metadata import extract_metadata


def test_extract_fn_metadata():
    source = """
@required(pip_install="path/requirements.txt", accel="A100:2", cpus=4, memory=16)
def my_function():
    pass

print("done")
    """
    decorator = ast.parse(source).body[0].decorator_list[0]
    metadata = extract_metadata(decorator, is_class_def=False)
    assert metadata is not None
    assert metadata.pip_install == "path/requirements.txt"
    assert metadata.resources.accel_type == "A100"
    assert metadata.resources.accel_count == 2
    assert metadata.resources.cpus == 4
    assert metadata.resources.memory == 16


def test_split_decorator():
    source = """
@required(pip_install="path/requirements.txt", accel="A100:2")
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
@required_fn(pip_install="path/requirements.txt", accel="A100:2")
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
    assert desc.metadata.pip_install == "path/requirements.txt"
    assert desc.metadata.resources.accel_type == "A100"
    assert desc.metadata.resources.accel_count == 2


def test_extract_desc_from_def_cls():
    source = """
@required_cls(pip_install="path/requirements.txt", accel="A100:2", entry="main_method")
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
    assert desc.metadata.pip_install == "path/requirements.txt"
    assert desc.metadata.resources.accel_type == "A100"
    assert desc.metadata.resources.accel_count == 2


def test_extract_desc_from_def_imports():
    source = """import torch
import requests
from PIL import Image
from typing import List
from declagent import required_fn

@required_fn(pip_install="path/requirements.txt", accel="A100:2")
def my_function():
    a: List[int] = [1, 2, 3]
    print("Using torch:", torch.__version__)
    print("Using PIL:", Image.__name__)
    """
    ast_node = ast.parse(source)
    descs = extract_desc(ast_node)

    desc = descs["my_function"]
    assert ast_eq(
        desc.ast_node,
        ast.parse("""def my_function():
    a: List[int] = [1, 2, 3]
    print('Using torch:', torch.__version__)
    print('Using PIL:', Image.__name__)""").body[0],
    )
    assert desc.metadata.pip_install == "path/requirements.txt"
    assert desc.metadata.resources.accel_type == "A100"
    assert desc.metadata.resources.accel_count == 2
    for imp, original_imp in zip(desc.imports, ast.parse(source).body[:5].__iter__()):
        assert ast_eq(imp, original_imp)
