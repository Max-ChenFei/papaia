import sys
import socket
import subprocess
from pathlib import Path
from venv import create

from ...IR import Desc, Node
from .another_process import AnotherProcess, split_pip_install


class VenvExecutor(AnotherProcess):
    """
    execution in a local Python virtual environment.
    """

    def stop(self, name: str) -> None:
        """Stop the running server."""
        super().stop(name)
        if name in self._processes:
            process = self._processes[name]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            del self._processes[name]

    def _deploy(self, node: Node, desc: Desc, generate_code: str) -> str:
        desc_dir = self._desc_dir(desc)
        venv = self._create_venv(desc_dir)

        port = pick_free_port()
        main_file = self._write_code_file(desc, generate_code, desc_dir, port)
        self._pip_install(venv, desc, desc_dir)
        self._py_run_background(venv, desc.ast_node.name, main_file)

        base_url = f"http://localhost:{port}"
        self._wait_for_server(base_url)

        return base_url

    def _create_venv(self, dir: Path):
        venv_path = dir / ".venv"
        create(str(venv_path), with_pip=True)
        return venv_path.resolve()

    def _pip_install(self, venv: Path, desc: Desc, desc_dir: Path) -> None:
        req_file, special_installs = split_pip_install(desc_dir, desc.pip_install)
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
                    # stdout=subprocess.DEVNULL,
                    # stderr=subprocess.DEVNULL,
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
                # Don't hide output so we can see errors
                # stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running background process: {e}")

        # Store process for cleanup in stop()
        if not hasattr(self, "_processes"):
            self._processes = {}
        self._processes[name] = process


def pick_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port
