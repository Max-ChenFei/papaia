import asyncio
import runpy
from pathlib import Path


from .IR import extract_desc
from .exec import place_on_exec_sites
from .cache import save_remote_cache_config
from .utils import read_ast, update_ast, write_ast, delete_file, ruff_fix

EXEC_NODE_CONFIG_FILENAME = "exec_nodes.toml"


def get_valid_nodes_path(nodes_path: Path | None = None) -> Path | None:
    if nodes_path is not None:
        if not nodes_path.exists():
            raise FileNotFoundError(
                f"Execution node config file not found: {nodes_path}"
            )
        return nodes_path
    path = Path(EXEC_NODE_CONFIG_FILENAME)
    if not path.exists():
        raise FileNotFoundError(
            f"No execution node configuration found. Please provide a valid path or create {EXEC_NODE_CONFIG_FILENAME} in the current directory."
        )
    return path


def compile_and_run(file_path: Path, nodes_path: Path | None = None) -> None:
    raw_ast = read_ast(file_path)
    desc = extract_desc(raw_ast)

    stub_ast, executors = asyncio.run(
        place_on_exec_sites(desc, get_valid_nodes_path(nodes_path))
    )
    new_ast = update_ast(raw_ast, stub_ast)
    compiled_file_path = file_path.with_name(file_path.stem + "_compiled.py")
    write_ast(new_ast, compiled_file_path)
    ruff_fix(compiled_file_path)
    save_remote_cache_config()

    try:
        runpy.run_path(str(compiled_file_path))
    finally:
        for tool, executor in executors.items():
            executor.stop(tool)

        delete_file(compiled_file_path)
