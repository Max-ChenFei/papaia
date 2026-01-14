import os
from pathlib import Path
from single_spec import available_nodes, Node


def test_available_exec_nodes_empty():
    original_dir = os.getcwd()
    try:
        # Change to a directory without exec_nodes.toml
        os.chdir(Path(__file__).parent.parent / "src")
        available_nodes()
    except FileNotFoundError as e:
        assert "No exec_nodes.toml found in current working directory" in str(e)
    finally:
        os.chdir(original_dir)


def test_available_exec_nodes_file():
    original_dir = os.getcwd()
    try:
        # Change to tests directory where exec_nodes.toml exists
        os.chdir(Path(__file__).parent)
        nodes, local_index = available_nodes()

        assert local_index == 0
        assert nodes is not None
        assert len(nodes) == 2
        # Check local node
        local_node = nodes[0]
        assert local_node.cpus == 8
        assert local_node.memory == 32
        assert local_node.accel_type == "A100"
        assert local_node.accel_count == 2

        # Check gpu_k8s node
        gpu_node = nodes[1]
        assert gpu_node.cpus == 32
        assert gpu_node.memory == 128
        assert gpu_node.accel_type == "A100"
        assert gpu_node.accel_count == 6
    finally:
        os.chdir(original_dir)


def test_get_accel_devices_allocates():
    n = Node(name="n1", executor="docker", accel_type="gpu", accel_count=4)

    devs = n.get_accel_devices(2)
    assert devs == "0,1"
    assert n.accel_assigned == [True, True, False, False]

    devs2 = n.get_accel_devices(1)
    assert devs2 == "2"
    assert n.accel_assigned == [True, True, True, False]


def test_release_accel_devices_frees():
    n = Node(name="n1", executor="docker", accel_type="gpu", accel_count=4)

    devs = n.get_accel_devices(3)
    assert devs == "0,1,2"
    assert n.accel_assigned == [True, True, True, False]

    n.release_accel_devices("1,2")
    assert n.accel_assigned == [True, False, False, False]

    devs = n.get_accel_devices(2)
    assert devs == "1,2"
