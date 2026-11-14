import ast
from pathlib import Path
import time

import requests

from .executor import Executor
from ..code_gen import func2fastapi, cls2fastapi
from ...IR import Desc, PipInstall, Node
from ...cache import LOCAL_CACHE_DIR
from ...utils import merge
from ...accel_assign import assign_accel_devices_code


class AnotherProcess(Executor):
    """
    execution in another execution environments (e.g., Docker, remote servers), not same as the CurrentProcess.
    """

    # cache for each desc including (code, pip requirements, venv)
    _cache: dict[str, Path] = {}
    _processes: dict[str, any] = {}

    def _generate_code(self, desc: Desc) -> tuple[list[str] | None, str | None, str]:
        if isinstance(desc.ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            pip_install, code_str, invoke_template = func2fastapi(desc.ast_node)
        elif isinstance(desc.ast_node, ast.ClassDef):
            pip_install, code_str, invoke_template = cls2fastapi(
                desc.ast_node,
                desc.metadata.entry,
                desc.metadata.setup,
                desc.metadata.teardown,
            )
        else:
            raise NotImplementedError(
                f"Unsupported AST node type: {type(desc.ast_node)}"
            )

        code = code_str
        if desc.imports:
            code = merge(ast.parse(code_str), desc.imports)
        code = f"{assign_accel_devices_code(desc.ast_node.name, desc.assigned_accel_devices)}\n{code}"
        return pip_install, code, invoke_template

    def _deploy(self, node: Node, desc: Desc, generate_code: str) -> str:
        raise NotImplementedError

    def _desc_dir(self, desc: Desc) -> Path:
        desc_dir = self._cache.get(desc.ast_node.name) or (
            LOCAL_CACHE_DIR / desc.ast_node.name
        )
        if not desc_dir.exists():
            desc_dir.mkdir(parents=True, exist_ok=True)
            self._cache[desc.ast_node.name] = desc_dir
        return desc_dir

    def _write_code_file(self, desc: Desc, code: str, dir: Path, port: int) -> Path:
        code_with_server = f"""{code}

if __name__ == "__main__":
    import uvicorn
    import sys
    import traceback
    try:
        print(f"Starting FastAPI server on port {port}...", flush=True)
        uvicorn.run(app, host="127.0.0.1", port={port}, log_level="info")
    except Exception as e:
        print(f"FATAL ERROR starting server: {{e}}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
"""
        main_file = dir / "main.py"
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(code_with_server)
        desc.append_pip_install(["uvicorn"])
        return main_file

    def _wait_for_server(
        self, base_url: str, timeout: int = 600, exit_code=None
    ) -> None:
        """Wait for the server to be ready.

        `exit_code` is an optional callable that returns the server process's exit
        code, or None while it runs; if the process exits first, fail at once
        instead of waiting for the timeout.
        """

        start_time = time.time()
        while time.time() - start_time < timeout:
            if exit_code is not None and (code := exit_code()) is not None:
                raise RuntimeError(
                    f"Server for {base_url} exited with code {code} before it was "
                    f"ready; see its output above"
                )
            if _server_ready(base_url):
                return
            time.sleep(0.1)
        raise TimeoutError(
            f"Server at {base_url} did not start within {timeout} seconds"
        )


def _server_ready(base_url: str) -> bool:
    try:
        return requests.get(f"{base_url}/docs", timeout=1).status_code == 200
    except requests.exceptions.RequestException:
        return False


LOCK_FILENAME = "requirements.lock.txt"


def write_lock_file(
    dir: Path, freeze_output: str, special_installs: list[tuple[str, str]] = ()
) -> Path:
    """Record the exact package versions installed in a tool's environment.

    The lock file can be passed back as ``pip_install="<path>"`` to reproduce the environment.
    Package indexes used for special installs (e.g., PyTorch CUDA wheels) are kept as
    ``--extra-index-url`` lines so the pinned versions can be resolved again.
    """
    lock_file = dir / LOCK_FILENAME
    index_lines = "".join(
        f"--extra-index-url {url}\n" for url in dict.fromkeys(u for _, u in special_installs)
    )
    lock_file.write_text(index_lines + freeze_output, encoding="utf-8")
    print(f"Recorded resolved package versions in {lock_file}", flush=True)
    return lock_file


def output_tail(text: str | None, lines: int = 30) -> str:
    return "\n".join((text or "").strip().splitlines()[-lines:])


def split_pip_install(
    dir: Path, pip_install: PipInstall | tuple[PipInstall, ...] | None
) -> tuple[Path, list[tuple[str, str]]]:
    """Write requirements and return (file, special_installs).

    special_installs: list of (package_spec, index_url) for packages that need specific indexes
    """
    req_file = dir / "requirements.txt"
    special_installs = []

    if pip_install is None:
        with open(req_file, "w", encoding="utf-8") as f:
            f.write("")
        return req_file, special_installs

    if not isinstance(pip_install, tuple):
        installs = (pip_install,)
    else:
        installs = pip_install

    regular_packages = []

    for install in installs:
        # a list of packages
        if isinstance(install, list):
            for pkg in install:
                # Check if package has index URL flags
                if "--index-url" in pkg or "--extra-index-url" in pkg:
                    parts = pkg.split()
                    pkg_name = parts[0]
                    # Find the URL after --index-url or --extra-index-url
                    for i, part in enumerate(parts):
                        if part in [
                            "--index-url",
                            "--extra-index-url",
                        ] and i + 1 < len(parts):
                            index_url = parts[i + 1]
                            special_installs.append((pkg_name, index_url))
                            break
                else:
                    regular_packages.append(pkg)
        # path to a requirements.txt file
        elif isinstance(install, str):
            src_path = Path(install)
            if src_path.exists():
                with open(src_path, "r", encoding="utf-8") as src:
                    regular_packages.extend(src.read().splitlines())
            else:
                raise FileNotFoundError(
                    f"Requirements file not found: {install} in current working dir {Path.cwd()}"
                )

    with open(req_file, "w", encoding="utf-8") as f:
        f.write("\n".join(regular_packages))

    return req_file, special_installs
