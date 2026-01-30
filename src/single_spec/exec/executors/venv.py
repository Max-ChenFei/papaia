import subprocess
import sys
import socket
import time
import requests
from string import Template
from pathlib import Path
from venv import create
from multiprocessing import Process

from ...IR import Desc, PipInstall
from .another_process import AnotherProcess
from ...cache import CACHE_PATH


class VenvExecutor(AnotherProcess):
    """
    execution in a local Python virtual environment.
    """

    # cache for each desc including (code, pip requirements, venv)
    _cache: dict[str, Path] = {}
    _processes: dict[str, Process] = {}

    def stop(self, name: str) -> None:
        """Stop the running FastAPI server."""
        super().stop(name)
        if name in self._processes:
            self._processes[name].terminate()
            self._processes[name].wait()
            del self._processes[name]

    def _deploy(self, desc: Desc, generate_code: str, invoke_template: Template) -> str:
        desc_dir = self._desc_dir(desc)
        self._venv_path = self._create_venv(desc_dir)

        port = pick_free_port()
        main_file, pip_packages = self._write_code_file(desc_dir, generate_code, port)
        desc.append_pip_install(pip_packages)

        req_file = self._write_pip_requirements_file(desc_dir, desc.pip_install)
        self._pip_install(self._venv_path, req_file)

        self._py_run_background(desc.ast_node.name, self._venv_path, main_file)

        # Wait for server to start
        base_url = f"http://localhost:{port}"
        self._wait_for_server(base_url)

        return invoke_template.substitute(base_url=base_url)

    def _desc_dir(self, desc: Desc) -> Path:
        desc_dir = self._cache.get(desc.ast_node.name) or (
            CACHE_PATH / desc.ast_node.name
        )
        if not desc_dir.exists():
            desc_dir.mkdir(parents=True, exist_ok=True)
            self._cache[desc.ast_node.name] = desc_dir
        return desc_dir

    def _write_code_file(self, dir, code: str, port: int) -> tuple[Path, list[str]]:
        code_with_server = f"""{code}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={port})
"""
        main_file = dir / "main.py"
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(code_with_server)
        pip_packages = ["uvicorn"]
        return main_file, pip_packages

    def _write_pip_requirements_file(
        self, dir, pip_install: PipInstall | tuple[PipInstall, ...] | None
    ) -> Path:
        req_file = dir / "requirements.txt"
        if pip_install is None:
            with open(req_file, "w", encoding="utf-8") as f:
                f.write("")
            return req_file

        if not isinstance(pip_install, tuple):
            installs = (pip_install,)

        for install in installs:
            # a list of packages
            if isinstance(install, list):
                with open(req_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(install))
            # path to a requirements.txt file
            elif isinstance(install, str):
                src_path = Path(install)
                if src_path.exists():
                    with (
                        open(src_path, "r", encoding="utf-8") as src,
                        open(req_file, "w", encoding="utf-8") as dst,
                    ):
                        dst.write(src.read())
                else:
                    raise FileNotFoundError(
                        f"Requirements file not found: {install} in current working dir {Path.cwd()}"
                    )
        return req_file

    def _create_venv(self, dir: Path) -> Path:
        venv_path = dir / ".venv"
        create(str(venv_path), with_pip=True)
        return venv_path

    def _pip_install(self, venv_path: Path, requirement_file: Path) -> None:
        py = venv_path.resolve()
        pip = (
            py / "Scripts" / "pip"
            if sys.platform == "win32"
            else venv_path / "bin" / "pip"
        )
        try:
            subprocess.run(
                [str(pip), "install", "-r", str(requirement_file)], check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")

    def _py_run_background(self, name, venv_path: Path, main_file: Path) -> None:
        py = venv_path.resolve()
        python = (
            py / "Scripts" / "python"
            if sys.platform == "win32"
            else venv_path / "bin" / "python"
        )
        try:
            # Run in background process
            process = subprocess.Popen([str(python), str(main_file)])
        except subprocess.CalledProcessError as e:
            print(f"Error running background process: {e}")

        # Store process for cleanup in stop()
        if not hasattr(self, "_processes"):
            self._processes = {}
        self._processes[name] = process

    def _wait_for_server(self, base_url: str, timeout: int = 100) -> None:
        """Wait for the server to be ready."""

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{base_url}/docs", timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                time.sleep(0.1)
        raise TimeoutError(
            f"Server at {base_url} did not start within {timeout} seconds"
        )


def pick_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port
