import ast
import socket

import pytest

from papaia.exec.executors.venv import VenvExecutor
from papaia.exec.executors.another_process import LOCK_FILENAME
from papaia.IR import Desc, Metadata

SERVER_CODE = """from fastapi import FastAPI
app = FastAPI()

@app.post("/ping")
def ping():
    return {"result": "pong"}
"""


def _desc(name: str, pip_install) -> Desc:
    return Desc(
        ast_node=ast.parse(f"def {name}():\n    pass\n").body[0],
        metadata=Metadata(pip_install=pip_install),
    )


def _lan_ip() -> str | None:
    """A non-loopback address of this machine, or None if there is none."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()
    return None if ip.startswith("127.") else ip


def test_failed_install_raises_with_pip_output():
    desc = _desc("bad_install_tool", ["this-package-does-not-exist-papaia-test==0.0.0"])
    with pytest.raises(RuntimeError) as err:
        VenvExecutor()._deploy(node=None, desc=desc, generate_code=SERVER_CODE)
    msg = str(err.value)
    assert "bad_install_tool" in msg
    assert "this-package-does-not-exist-papaia-test" in msg


def test_lock_file_and_loopback_binding():
    desc = _desc("lock_tool", ["fastapi", "uvicorn", "pydantic"])
    executor = VenvExecutor()
    base_url = executor._deploy(node=None, desc=desc, generate_code=SERVER_CODE)
    try:
        lock = executor._desc_dir(desc) / LOCK_FILENAME
        assert lock.exists()
        pinned = lock.read_text().lower()
        assert "fastapi==" in pinned and "uvicorn==" in pinned

        port = int(base_url.rsplit(":", 1)[1])
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass  # reachable on loopback
        ip = _lan_ip()
        if ip is not None:  # not reachable from the network
            with pytest.raises(OSError):
                socket.create_connection((ip, port), timeout=2).close()
    finally:
        executor.stop(desc.ast_node.name)


def test_assignment_with_node_without_accelerators(tmp_path):
    """Regression: a node that declares no accelerator must not break placement."""
    from papaia.exec.place import assignment
    from papaia.IR import available_nodes
    from papaia.IR.resources import Resources

    cfg = tmp_path / "exec_nodes.toml"
    cfg.write_text('[nodes.local]\nlocation = "local"\ncpus = 8\nmemory = 32\n')
    nodes, local_index = available_nodes(cfg)
    desc = _desc("plain_tool", None)
    desc.metadata.resources = Resources()
    assert assignment([desc], nodes, local_index=local_index) == {0: local_index}
