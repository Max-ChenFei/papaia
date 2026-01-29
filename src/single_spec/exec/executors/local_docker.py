import os
import re
import time
import socket
import tempfile
import subprocess
import shutil
from string import Template
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from .another_process import AnotherProcess
from ...IR import Desc, Node


@dataclass
class ServiceHandle:
    container_id: str
    base_url: str
    src_dir: TemporaryDirectory = field(repr=False)

    def stop(self) -> None:
        try:
            run_cmd("docker", "rm", "-f", self.container_id)
        except Exception:
            pass
        self.src_dir.cleanup()


class LocalDocker(AnotherProcess):
    """
    execution in local Docker containers.
    """

    services: dict[str, ServiceHandle] = {}
    assigned_gpus: dict[int, bool] = {}

    def stop(self, name: str) -> None:
        super().stop(name)
        service = self.services.get(name)
        if service:
            service.stop()
            del self.services[name]

    def _deploy(self, desc: Desc, generate_code: str, invoke_template: Template) -> str:
        if shutil.which("docker") is None:
            raise RuntimeError("Docker executable not found in PATH")
        service = start_fastapi_service(generate_code, desc)
        self.services[desc.ast_node.name] = service
        return invoke_template.substitute(base_url=service.base_url)


def start_fastapi_service(
    service_code: str,
    desc: Desc,
) -> ServiceHandle:
    docker_image = desc.env if isinstance(desc.env, str) else desc.env[0]
    cpus = desc.resources.cpus
    memory = desc.resources.memory

    td = tempfile.TemporaryDirectory()
    run_path = os.path.join(td.name, "run.py")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(service_code)
    mount_path = os.path.abspath(td.name)

    # Simple "no-build" run: installs deps at container start (slow but easy)
    host_port = pick_free_port()

    cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "-p",
        f"{host_port}:8000",
        "--name",
        f"svc_{host_port}",
        "-v",
        f"{mount_path}:/app",
        "-w",
        "/app",
        f"{docker_image}",
        "bash",
        "-lc",
        f"ls -la /app && pip install fastapi uvicorn {' '.join(desc.env[1]) if isinstance(desc.env, tuple) and desc.env[1] is not None else ''} && uvicorn run:app --host 0.0.0.0 --port 8000",
    ]
    if cpus is not None and cpus > 0:
        cmd.extend(["--cpus", str(cpus)])
    if memory is not None and memory > 0:
        cmd.extend(["--memory", f"{memory}m"])

    run_cmd("docker", "pull", docker_image)
    container_id = run_cmd(*cmd)
    if not container_id:
        raise RuntimeError("Failed to get container ID from docker run")

    base_url = f"http://127.0.0.1:{host_port}"
    try:
        wait_for_container_ready(container_id, timeout_s=3000)
    except Exception as e:
        # if it didn't come up, stop container and re-raise
        try:
            run_cmd("docker", "rm", "-f", container_id)
        except Exception:
            pass
        td.cleanup()
        raise RuntimeError(f"Service failed to start in Docker container: {e}")

    return ServiceHandle(container_id, base_url, td)


def accel_devices_from_node(desc: Desc, node: Node) -> str | None:
    if (
        desc.resources.accel_type is not None
        and desc.resources.accel_count is not None
        and desc.resources.accel_count > 0
    ):
        accel_devices = node.get_accel_devices(desc.resources.accel_count)
    else:
        accel_devices = None
    return accel_devices


def pick_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run_cmd(*args: str) -> str:
    """Run a command (blocking) and return stdout; raise on non-zero exit."""
    cp = subprocess.run(args, text=True, capture_output=True)
    if cp.returncode != 0:
        raise RuntimeError(f"Command failed ({cp.returncode}): {' '.join(args)}")
    return cp.stdout.strip()


READY_RE = re.compile(r"Uvicorn running on http://0\.0\.0\.0:8000", re.IGNORECASE)
ERROR_MARKERS = (
    "ERROR:",
    "Error loading ASGI app",
    "ModuleNotFoundError:",
    "ImportError:",
)


def wait_for_container_ready(container_id: str, timeout_s: int = 3000) -> None:
    """
    Stream `docker logs -f` until we see a readiness line, or an error line, or timeout.
    Raises RuntimeError on error/timeout.
    """
    p = subprocess.Popen(
        ["docker", "logs", "-f", container_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    start = time.time()
    tail = []  # keep last N lines for context
    try:
        for line in p.stdout:
            tail.append(line.rstrip("\n"))
            if len(tail) > 200:
                tail.pop(0)

            # detect readiness
            if READY_RE.search(line):
                return

            # detect common errors
            if any(m in line for m in ERROR_MARKERS):
                raise RuntimeError(
                    "Service failed to start. Logs:\n" + "\n".join(tail[-80:])
                )

            # timeout check
            if time.time() - start > timeout_s:
                raise RuntimeError(
                    f"Timed out waiting for service to start after {timeout_s:.1f}s. Logs:\n"
                    + "\n".join(tail[-80:])
                )

        # If we exit the loop, docker logs ended (container exited)
        rc = p.wait(timeout=2)
        raise RuntimeError(
            f"Container exited before becoming ready (docker logs ended, rc={rc}). Logs:\n"
            + "\n".join(tail[-80:])
        )

    finally:
        # stop following logs if still running
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()
