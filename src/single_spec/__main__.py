import argparse
from pathlib import Path

from .compile_and_run import compile_and_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Python file.")
    parser.add_argument("file", help="Path to the Python file to compile and run")
    args = parser.parse_args()

    path = Path(args.file).resolve()
    compile_and_run(path)


if __name__ == "__main__":
    main()
