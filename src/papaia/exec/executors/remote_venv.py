import sys
import asyncio
import threading
import asyncssh
from pathlib import Path

from .another_process import (
    AnotherProcess,
    split_pip_install,
    write_lock_file,
    output_tail,
)
from ...IR import Desc, Node
from ...cache import add_remote_cache, REMOTE_CACHE_DIR


class RemoteVenv(AnotherProcess):
    """
    execution in a remote Python virtual environment over SSH.
    """

    _processes: dict[str, dict] = {}

    def stop(self, name):
        super().stop(name)
        if name in self._processes:
            proc_info = self._processes[name]
            if proc_info.get("tunnel") is not None:
                proc_info["tunnel"].close()
            asyncio.run(self._stop_remote(proc_info))
            del self._processes[name]

    async def _stop_remote(self, proc_info):
        node = proc_info["node"]
        remote_dir = proc_info["remote_dir"]

        async with asyncssh.connect(
            host=node.host, port=node.port, username=node.username
        ) as conn:
            # Kill the server by the PID recorded at startup.
            cmd = f"kill $(cat {remote_dir}/server.pid)"
            result = await conn.run(cmd, check=False)
            if result.exit_status == 0:
                _print_flush(f"Stopped remote server at {remote_dir}")
            else:
                _print_flush(
                    f"Error stopping remote server at {remote_dir}: "
                    f"{(result.stderr or result.stdout).strip()}"
                )

    def _deploy(self, node: Node, desc: Desc, generate_code: str) -> str:
        desc_dir = self._desc_dir(desc)
        base_url = asyncio.run(self.deploy_remote(node, desc, desc_dir, generate_code))
        return base_url

    async def deploy_remote(
        self,
        node: Node,
        desc: Desc,
        desc_dir: Path,
        generate_code: str,
    ):
        _print_flush(f"\n{'=' * 60}")
        _print_flush(f"STARTING REMOTE DEPLOYMENT: {desc.ast_node.name}")
        _print_flush(f"{'=' * 60}")
        try:
            _print_flush(f"Connecting to {node.host}:{node.port} via SSH...")
            async with asyncssh.connect(
                host=node.host, port=node.port, username=node.username
            ) as conn:
                _print_flush(f"✓ Connected to {node.host}:{node.port} via SSH")
                _print_flush("Allocating remote port...")
                result = await conn.run(
                    "python3 -c 'import socket; s=socket.socket(); s.bind((\"\",0)); print(s.getsockname()[1])'",
                    check=True,
                )
                port = int(result.stdout.strip())
                _print_flush(f"✓ Allocated remote port {port} on {node.host}")

                _print_flush("Writing code and preparing requirements...")
                main_file = self._write_code_file(desc, generate_code, desc_dir, port)
                req_file, special_installs = split_pip_install(
                    desc_dir, desc.pip_install
                )

                remote_dir = f"{REMOTE_CACHE_DIR}/{desc.ast_node.name}"

                _print_flush(f"Creating remote directory {remote_dir}...")
                await conn.run(f"mkdir -p {remote_dir}", check=True)
                _print_flush("Uploading files via SFTP...")
                async with await conn.start_sftp_client() as sftp:
                    await sftp.put(str(req_file), f"{remote_dir}/requirements.txt")
                    await sftp.put(str(main_file), f"{remote_dir}/main.py")
                _print_flush(f"✓ Copied code to remote directory {remote_dir}")
                add_remote_cache(node, remote_dir)

                # Create venv
                _print_flush(f"Creating virtual environment...")
                cmd = f"python3 -m venv {remote_dir}/.venv"
                await conn.run(cmd, check=True)
                _print_flush(f"✓ Created venv at {remote_dir}/.venv")

                # Install special packages with specific indexes first
                if special_installs:
                    _print_flush(
                        f"Installing {len(special_installs)} special package(s)..."
                    )
                for pkg, index_url in special_installs:
                    _print_flush(f"  Installing {pkg} from {index_url}...")
                    cmd = (
                        f"bash -lc '"
                        f"source {remote_dir}/.venv/bin/activate && "
                        f"pip install {pkg} --index-url {index_url} --verbose"
                        f"'"
                    )
                    r2 = await conn.run(cmd, check=False)
                    if r2.exit_status == 0:
                        _print_flush(f"    ✓ Installed {pkg}")
                    else:
                        _print_flush(f"    ✗ Failed to install {pkg}")
                        _print_flush(f"    stdout: {r2.stdout}")
                        _print_flush(f"    stderr: {r2.stderr}")
                        raise RuntimeError(
                            f"pip install {pkg} failed for tool '{desc.ast_node.name}' "
                            f"on {node.host}:\n{output_tail(r2.stderr or r2.stdout)}"
                        )

                # Install regular packages from requirements.txt
                _print_flush(f"Installing packages from requirements.txt...")
                cmd = (
                    f"bash -lc '"
                    f"source {remote_dir}/.venv/bin/activate && "
                    f"pip install -r {remote_dir}/requirements.txt --verbose"
                    f"'"
                )
                r3 = await conn.run(cmd, check=False)
                if r3.exit_status == 0:
                    _print_flush(f"✓ Installed all requirements")
                else:
                    raise RuntimeError(
                        f"pip install failed for tool '{desc.ast_node.name}' on "
                        f"{node.host} (exit code {r3.exit_status}):\n"
                        f"{output_tail(r3.stderr or r3.stdout)}"
                    )
                freeze = await conn.run(
                    f"{remote_dir}/.venv/bin/pip freeze", check=True
                )
                write_lock_file(desc_dir, freeze.stdout, special_installs)

                # Run the server in background
                _print_flush("Starting server...")

                cmd = (
                    f"sh -c 'cd {remote_dir} && "
                    f"nohup {remote_dir}/.venv/bin/python main.py > {remote_dir}/server.log 2>&1 < /dev/null & "
                    f"echo $! > {remote_dir}/server.pid'"
                )
                r4 = await conn.run(cmd, check=False)
                if r4.exit_status != 0:
                    _print_flush(f"  ✗ Failed to start server command")
                    _print_flush(f"  stdout: {r4.stdout}")
                    _print_flush(f"  stderr: {r4.stderr}")
                    sys.stdout.flush()
                    raise Exception("Failed to start server process")

                sys.stdout.flush()

                # Register now so the server is stopped even if a later step fails.
                self._processes[desc.ast_node.name] = {
                    "node": node,
                    "remote_dir": remote_dir,
                    "tunnel": None,
                }

                # The service listens on the remote loopback interface only; the agent
                # reaches it through an SSH port forward, so it is not exposed on the
                # network and traffic is encrypted and authenticated by SSH.
                tunnel = SSHTunnel(node, port)
                self._processes[desc.ast_node.name]["tunnel"] = tunnel
                base_url = f"http://127.0.0.1:{tunnel.local_port}"

                _print_flush("  Waiting for server to start...")
                try:
                    self._wait_for_server(base_url)
                except TimeoutError as e:
                    log = await conn.run(
                        f"tail -100 {remote_dir}/server.log", check=False
                    )
                    raise TimeoutError(
                        f"Tool '{desc.ast_node.name}' did not start on {node.host}: "
                        f"{e}\nRecent server log:\n{log.stdout}"
                    ) from e
                _print_flush(f"  ✓ Server reachable via SSH tunnel at {base_url}")
                self._processes[desc.ast_node.name]["base_url"] = base_url
                return base_url
        except asyncssh.ProcessError as e:
            _print_flush(f"\n[ERROR] Command failed with exit status {e.exit_status}")
            _print_flush(f"[ERROR] Command: {e.command}")
            if e.stdout:
                _print_flush(f"[ERROR] stdout:\n{e.stdout}")
            if e.stderr:
                _print_flush(f"[ERROR] stderr:\n{e.stderr}")
            raise


def _print_flush(msg):
    """Print with immediate flush to ensure output appears in notebooks."""
    print(msg, flush=True)
    sys.stdout.flush()


class SSHTunnel:
    """Local port forward 127.0.0.1:<local_port> -> remote 127.0.0.1:<remote_port> over SSH.

    Runs on its own event loop thread so it stays open while the agent program runs.
    """

    def __init__(self, node, remote_port: int, timeout: float = 30):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._conn = None
        try:
            self.local_port = asyncio.run_coroutine_threadsafe(
                self._open(node, remote_port), self._loop
            ).result(timeout)
        except Exception:
            self.close()
            raise

    async def _open(self, node, remote_port: int) -> int:
        self._conn = await asyncssh.connect(
            host=node.host, port=node.port, username=node.username
        )
        listener = await self._conn.forward_local_port(
            "127.0.0.1", 0, "127.0.0.1", remote_port
        )
        return listener.get_port()

    async def _close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            await self._conn.wait_closed()

    def close(self) -> None:
        if self._loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(self._close(), self._loop).result(10)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        if not self._thread.is_alive():
            self._loop.close()
