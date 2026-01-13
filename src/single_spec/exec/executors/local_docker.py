import os
import time
import socket
import tempfile
import requests
from asyncio import subprocess
from string import Template

from ...IR import Desc
from .another_process import AnotherProcess


class ServiceHandle:
    def __init__(self, container_id: str, base_url: str, workdir: str):
        self.container_id = container_id
        self.base_url = base_url
        self.workdir = workdir

    def stop(self):
        subprocess.run(["docker", "rm", "-f", self.container_id], check=False)


class LocalDocker(AnotherProcess):
    """
    execution in local Docker containers.
    """

    services: dict[str, ServiceHandle] = {}

    def stop(self, name: str) -> None:
        service = self.services.get(name)
        if service:
            service.stop()
            del self.services[name]

    def _deploy(self, desc: Desc, generate_code: str, invoke_template: Template) -> str:
        service = start_service(
            generate_code,
            cpus=desc.resources.cpus,
            memory=desc.resources.memory,
            docker_image=desc.env,
        )
        self.services[desc.ast_node.name] = service
        return invoke_template.substitute(base_url=service.base_url)


def pick_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_up(base_url: str, timeout_s: int = 20):
    start = time.time()
    while True:
        try:
            r = requests.get(base_url + "/docs", timeout=1)
            if r.status_code in (200, 404):
                return
        except Exception:
            pass
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Service not up: {base_url}")
        time.sleep(0.3)


def start_service(service_code: str, cpus, memory, docker_image) -> ServiceHandle:
    td = tempfile.TemporaryDirectory()
    run_path = os.path.join(td.name, "run.py")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(service_code)

    host_port = pick_free_port()

    # Simple "no-build" run: installs deps at container start (slow but easy)
    cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--cpus",
        f"{cpus}",
        "--memory",
        f"{memory}m",
        "-p",
        f"{host_port}:8000",
        "--name",
        f"svc_{host_port}",
        "-v",
        f"{td.name}:/app:ro",
        "-w",
        "/app",
        f"{docker_image}",
        "bash",
        "-lc",
        "pip install -q fastapi uvicorn && uvicorn run:app --host 0.0.0.0 --port 8000",
    ]
    container_id = subprocess.check_output(cmd, text=True).strip()
    base_url = f"http://127.0.0.1:{host_port}"

    wait_up(base_url)
    return ServiceHandle(container_id, base_url, td)
