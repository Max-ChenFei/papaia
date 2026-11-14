import sys
import socket
import subprocess
from pathlib import Path
from venv import create

from ...IR import Desc, Node
from .another_process import AnotherProcess, split_pip_install, write_lock_file, output_tail


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
        process = self._processes[desc.ast_node.name]
        self._wait_for_server(base_url, exit_code=process.poll)

        return base_url

    def _create_venv(self, dir: Path):
        venv_path = dir / ".venv"
        create(str(venv_path), with_pip=True)
        return venv_path.resolve()

    def _pip_install(self, venv: Path, desc: Desc, desc_dir: Path) -> None:
        req_file, special_installs = split_pip_install(desc_dir, desc.pip_install)
        name = desc.ast_node.name
        pip = venv / "Scripts" / "pip" if sys.platform == "win32" else venv / "bin" / "pip"
        for pkg, index_url in special_installs:
            print(f"Installing {pkg} from {index_url}")
            _run_pip(pip, ["install", pkg, "--index-url", index_url], name)
        _run_pip(pip, ["install", "-r", str(req_file)], name)
        write_lock_file(desc_dir, _run_pip(pip, ["freeze"], name), special_installs)

    def _py_run_background(self, py: Path, name, main_file: Path) -> None:
        python = (
            py / "Scripts" / "python"
            if sys.platform == "win32"
            else py / "bin" / "python"
        )
        # Output is not captured, so the server's errors appear in the terminal.
        process = subprocess.Popen([str(python), str(main_file)])

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


def _run_pip(pip: Path, args: list[str], tool: str) -> str:
    """Run pip; raise with pip's own error output if it fails, so `papaia run` stops early."""
    r = subprocess.run([str(pip), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"pip {' '.join(args)} failed for tool '{tool}' "
            f"(exit code {r.returncode}):\n{output_tail(r.stderr or r.stdout)}"
        )
    return r.stdout
