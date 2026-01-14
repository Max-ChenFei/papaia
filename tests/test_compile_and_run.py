import os
from pathlib import Path
import tempfile

from single_spec import compile_and_run


def test_local_inprocess(mocker, capsys):
    original_dir = os.getcwd()

    src = '''from single_spec import required

@required(accel="A100:1")
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


def test_local_docker_func(mocker, capsys):
    original_dir = os.getcwd()

    src = '''from single_spec import required

@required(accel="A100:1", env="python:3.9-slim")
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


def test_local_docker_cls(mocker, capsys):
    original_dir = os.getcwd()

    src = '''from single_spec import required

@required(accel="A100:1", entry="get_weather", env="python:3.9-slim")
class WeatherService:
    def get_weather(self, city: str) -> str:
        """Get weather for a given city.
        Args:
            city: The city to get the weather for.
        """
        return f"It's always sunny in {city}!"

print(WeatherService().get_weather("San Francisco"))
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


def test_local_inprocess_docker_func(mocker, capsys):
    original_dir = os.getcwd()

    src = '''from single_spec import required
@required(accel="A100:1")
def get_weather2(city: str) -> str:
    """Get weather for a given city.
    Args:
        city: The city to get the weather for.
    """
    return f"It's always sunny in {city}2!"

@required(accel="A100:1", env="python:3.9-slim")
def get_weather(city: str) -> str:
    """Get weather for a given city.
    Args:
        city: The city to get the weather for.
    """
    return f"It's always sunny in {city}!"

print(get_weather2("San Francisco"))
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
            assert "It's always sunny in San Francisco2!" in captured.out
            assert "It's always sunny in San Francisco!" in captured.out

    finally:
        os.chdir(original_dir)
