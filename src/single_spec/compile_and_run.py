import runpy
from pathlib import Path

from .IR import extract_desc
from .exec import place_on_exec_sites
from .utils import read_ast, update_ast, write_ast, delete_file, ruff_fix


def compile_and_run(file_path: Path):
    raw_ast = read_ast(file_path)
    desc = extract_desc(raw_ast)
    stub_ast, executors = place_on_exec_sites(desc)
    new_ast = update_ast(raw_ast, stub_ast)
    compiled_file_path = file_path.with_name(file_path.stem + "_compiled.py")
    write_ast(new_ast, compiled_file_path)
    ruff_fix(compiled_file_path)
    try:
        runpy.run_path(str(compiled_file_path))
    finally:
        for tool, executor in executors.items():
            executor.stop(tool)

        delete_file(compiled_file_path)
