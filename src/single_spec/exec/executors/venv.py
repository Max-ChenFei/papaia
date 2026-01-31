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
        """Stop the running server."""
        super().stop(name)
        print(f"Stopping VenvExecutor for {name}")
        if name in self._processes:
            process = self._processes[name]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            del self._processes[name]

    def _deploy(self, desc: Desc, generate_code: str, invoke_template: Template) -> str:
        desc_dir = self._desc_dir(desc)
        venv = self._create_venv(desc_dir)

        port = pick_free_port()
        main_file = self._write_code_file(desc, generate_code, desc_dir, port)
        self._pip_install(venv, desc, desc_dir)
        self._py_run_background(venv, desc.ast_node.name, main_file)

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

    def _write_code_file(self, desc: Desc, code: str, dir: Path, port: int) -> Path:
        code_with_server = f"""{code}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={port})
"""
        main_file = dir / "main.py"
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(code_with_server)
        desc.append_pip_install(["uvicorn"])
        return main_file

    def _split_pip_install(
        self, dir, pip_install: PipInstall | tuple[PipInstall, ...] | None
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

    def _create_venv(self, dir: Path):
        venv_path = dir / ".venv"
        create(str(venv_path), with_pip=True)
        return venv_path.resolve()

    def _pip_install(self, venv: Path, desc: Desc, desc_dir: Path) -> None:
        req_file, special_installs = self._split_pip_install(desc_dir, desc.pip_install)
        self._pip_install_from_index(venv, special_installs)
        self._pip_install_from_requirements(venv, req_file)

    def _pip_install_from_index(
        self, py: Path, special_installs: list[tuple[str, str]]
    ) -> None:
        """Install a specific package from a specific index."""
        pip = py / "Scripts" / "pip" if sys.platform == "win32" else py / "bin" / "pip"
        for pkg, index_url in special_installs:
            try:
                print(f"Installing {pkg} from {index_url}")
                subprocess.run(
                    [str(pip), "install", pkg, "--index-url", index_url],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError as e:
                print(f"Error installing {pkg}: {e}")

    def _pip_install_from_requirements(self, py: Path, req_file: Path) -> None:
        """Install packages from a requirements.txt file."""
        pip = py / "Scripts" / "pip" if sys.platform == "win32" else py / "bin" / "pip"
        try:
            subprocess.run(
                [str(pip), "install", "-r", str(req_file)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages from {req_file}: {e}")

    def _py_run_background(self, py: Path, name, main_file: Path) -> None:
        python = (
            py / "Scripts" / "python"
            if sys.platform == "win32"
            else py / "bin" / "python"
        )
        try:
            # Run in background process
            process = subprocess.Popen(
                [str(python), str(main_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
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
