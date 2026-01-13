import os
from pathlib import Path

from single_spec import compile_and_run
from single_spec.utils import read_ast, delete_file

from ast_eq import ast_eq


def test_compiler_all_local(mocker):
    original_dir = os.getcwd()

    # Mock only runpy to prevent actual execution
    mock_runpy = mocker.patch("single_spec.compiler.runpy.run_path")
    mock_delete_file = mocker.patch("single_spec.compiler.delete_file")

    try:
        # Change to tests directory where exec_nodes.toml exists
        os.chdir(Path(__file__).parent)

        file_path = Path(__file__).parent / "example.py"
        compile_and_run(file_path)

        # Verify the compiled file was run
        compiled_file_path = file_path.with_name(file_path.stem + "_compiled.py")
        mock_runpy.assert_called_once_with(str(compiled_file_path))
        mock_delete_file.assert_called_once_with(compiled_file_path)

        # Compare AST instead of text (to ignore quote style differences)
        original_ast = read_ast(file_path)
        compiled_ast = read_ast(compiled_file_path)

        assert ast_eq(original_ast, compiled_ast), (
            "Compiled file should have same AST as original"
        )
    finally:
        delete_file(compiled_file_path)
        os.chdir(original_dir)
