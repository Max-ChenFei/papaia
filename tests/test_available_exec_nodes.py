import os
from pathlib import Path
from single_spec import available_exec_nodes


def test_available_exec_nodes_empty():
    original_dir = os.getcwd()
    try:
        # Change to a directory without exec_nodes.toml
        os.chdir(Path(__file__).parent.parent / "src")
        default_node, nodes = available_exec_nodes()
        assert default_node is None
        assert nodes == []
    finally:
        os.chdir(original_dir)


def test_available_exec_nodes_file():
    original_dir = os.getcwd()
    try:
        # Change to tests directory where exec_nodes.toml exists
        os.chdir(Path(__file__).parent)
        default_node, nodes = available_exec_nodes()

        assert default_node == "local"
        assert len(nodes) == 2

        # Check local node
        local_node = next(n for n in nodes if n.name == "local")
        assert local_node.resources.cpus == 8
        assert local_node.resources.memory == 32
        assert local_node.resources.accel == "A100:1"

        # Check gpu_k8s node
        gpu_node = next(n for n in nodes if n.name == "gpu_k8s")
        assert gpu_node.resources.cpus == 32
        assert gpu_node.resources.memory == 128
        assert gpu_node.resources.accel == "A100:6"
    finally:
        os.chdir(original_dir)
