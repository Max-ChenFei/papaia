import os
from pathlib import Path
import tempfile

from single_spec import compile_and_run


def test_local_inprocess(mocker, capsys):
    original_dir = os.getcwd()

    src = '''from single_spec import required_fn

@required_fn(accel="A100:1")
def get_weather(city: str) -> str:
    """Get weather for a given city.
    Args:
        city: The city to get the weather for.
    """
    return f"It's always sunny in {city}!"

print(get_weather("San Francisco"))
'''

    try:
        # Change to tests directory where exec_nodes.toml exists
        os.chdir(Path(__file__).parent)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "example_out.py"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(src)

            compile_and_run(tmp_file)

            captured = capsys.readouterr()
            assert "It's always sunny in San Francisco!" in captured.out

    finally:
        os.chdir(original_dir)


def test_venv_executor(capsys):
    original_dir = os.getcwd()

    src = '''from single_spec import required_fn
import requests

@required_fn(pip_install=["requests"])
def get_weather(city: str) -> str:
    """Get weather for a given city.
    Args:
        city: The city to get the weather for.
    """
    return f"It's always sunny in {city} with requests {requests.__version__}!"

print(get_weather("San Francisco"))
'''

    try:
        # Change to tests directory where exec_nodes.toml exists
        os.chdir(Path(__file__).parent)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "example_out.py"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(src)

            compile_and_run(tmp_file)

            captured = capsys.readouterr()
            assert "It's always sunny in San Francisco with requests" in captured.out

    finally:
        os.chdir(original_dir)
