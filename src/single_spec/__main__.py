import argparse
from pathlib import Path

from .compile_and_run import compile_and_run
from .cache import clear_cache


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-spec CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a Python file")
    run_parser.add_argument("file", help="Path to the Python file to compile and run")

    # Clear cache command
    subparsers.add_parser("clear-cache", help="Clear the cache directory")

    args = parser.parse_args()

    if args.command == "run":
        path = Path(args.file).resolve()
        compile_and_run(path)
    elif args.command == "clear-cache":
        clear_cache()
    else:
        # Default behavior for backward compatibility
        if hasattr(args, "file"):
            path = Path(args.file).resolve()
            compile_and_run(path)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
