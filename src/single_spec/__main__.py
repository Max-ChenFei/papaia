import argparse
from pathlib import Path

from .compile_and_run import compile_and_run
from .cache import clear_cache


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-spec CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    run_parser = subparsers.add_parser("run", help="Run a Python file")
    run_parser.add_argument("file", help="Path to the Python file to compile and run")
    subparsers.add_parser("clear", help="Clear the cache directory")
    args = parser.parse_args()

    if args.command == "run":
        path = Path(args.file).resolve()
        compile_and_run(path)
    elif args.command == "clear":
        clear_cache()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
