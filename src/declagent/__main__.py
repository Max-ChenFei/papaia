import argparse
from pathlib import Path

from .compile_and_run import compile_and_run
from .cache import clear_cache


def main() -> None:
    parser = argparse.ArgumentParser(description="decl CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    run_parser = subparsers.add_parser("run", help="Run a Python file")
    run_parser.add_argument("file", help="Path to the Python file to compile and run")
    run_parser.add_argument(
        "--config",
        "-c",
        help="Path to execution nodes config file (default: exec_nodes.toml in same directory as file)",
        default=None,
    )
    subparsers.add_parser("clear", help="Clear the cache directory")
    args = parser.parse_args()

    if args.command == "run":
        path = Path(args.file).resolve()
        compile_and_run(path, Path(args.config) if args.config else None)
    elif args.command == "clear":
        clear_cache()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
