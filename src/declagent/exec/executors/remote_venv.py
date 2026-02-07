import sys
import asyncio
import asyncssh
from pathlib import Path

from .another_process import AnotherProcess, split_pip_install
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
            asyncio.run(self._stop_remote(proc_info))
            del self._processes[name]

    async def _stop_remote(self, proc_info):
        node = proc_info["node"]
        remote_dir = proc_info["remote_dir"]

        async with asyncssh.connect(
            host=node.host,
            port=node.port,
            username=node.username,
            password=node.password,
        ) as conn:
            cmd = f"pkill -f '{remote_dir}/main.py'"
            try:
                await conn.run(cmd)
                _print_flush(f"Stopped remote server at {remote_dir}")
            except Exception as e:
                _print_flush(f"Error stopping remote server: {e}")

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
                host=node.host,
                port=node.port,
                username=node.username,
                password=node.password,
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
                        raise Exception(f"Failed to install {pkg}")

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
                    _print_flush(f"✗ Failed to install requirements")
                    _print_flush(f"  stdout: {r3.stdout}")
                    _print_flush(f"  stderr: {r3.stderr}")

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

                base_url = f"http://{node.host}:{port}"

                # Wait for server to be ready on the remote machine first
                _print_flush("  Waiting for server to start...")

                # todo: better logging here
                # Check server logs for any startup issues
                log_result = await conn.run(
                    f"cat {remote_dir}/server.log 2>&1", check=False
                )
                if log_result.stdout:
                    _print_flush(f"  Server startup logs:\n{log_result.stdout}")

                # Now try to connect from local machine (may fail due to firewall)
                _print_flush(
                    f"  Testing connectivity from local machine to {base_url}..."
                )

                try:
                    self._wait_for_server(base_url)
                    _print_flush(
                        f"  ✓ Server is accessible from local machine at {base_url}"
                    )
                except TimeoutError as e:
                    # Show more logs if connection fails
                    _print_flush(f"  ✗ Connection timeout: {e}")
                    log_result2 = await conn.run(
                        f"cat {remote_dir}/server.log 2>&1 | tail -100", check=False
                    )
                    if log_result2.stdout:
                        _print_flush(f"  Recent server logs:\n{log_result2.stdout}")
                    if log_result2.stdout:
                        _print_flush(f"  Recent server logs:\n{log_result2.stdout}")
                    _print_flush(
                        "  ⚠ Warning: Cannot connect from local machine (firewall/network issue)"
                    )
                    _print_flush(
                        "  ⚠ Server is running on remote machine but not accessible externally"
                    )
                    _print_flush(
                        "  ⚠ You may need to configure firewall or use SSH tunneling"
                    )
                    sys.stdout.flush()
                    # Don't fail - server is running, just not accessible from local machine

                self._processes[desc.ast_node.name] = {
                    "node": node,
                    "remote_dir": remote_dir,
                    "base_url": base_url,
                }
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
