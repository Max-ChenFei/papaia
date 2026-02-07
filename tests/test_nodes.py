import os
from pathlib import Path

from single_spec.IR import available_nodes, Node


def test_get_valid_nodes_path():
    try:
        # Change to a directory without exec_nodes.toml
        os.chdir(Path(__file__).parent.parent / "src")
        path = Path(__file__).parent / "no_exec_nodes.toml"
        available_nodes(path)
    except FileNotFoundError as e:
        assert "No such file or directory" in str(e)


def test_available_exec_nodes_file():
    path = Path(__file__).parent / "exec_nodes.toml"
    nodes, local_index = available_nodes(path)

    assert local_index == 0
    assert nodes is not None
    assert len(nodes) == 2
    # Check local node
    local_node = nodes[0]
    assert local_node.cpus == 8
    assert local_node.memory == 32
    assert local_node.accel_type == "A100"
    assert local_node.accel_count == 2

    # Check vm1 node
    vm1 = nodes[1]
    assert vm1.cpus == 32
    assert vm1.memory == 128
    assert vm1.accel_type == "A100"
    assert vm1.accel_count == 6
    assert vm1.host == "gpu-cluster.example.com"
    assert vm1.port == 22
    assert vm1.username == "user"
    assert vm1.password == "123456"


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
