import ast
import pytest

from decl.IR import Node
from decl.exec.place import assignment
from decl.IR import Desc, Metadata, Resources


@pytest.fixture
def tasks():
    mock = ast.parse("def foo(): pass")
    return [
        Desc(
            mock,
            metadata=Metadata(
                resources=Resources(cpus=2, memory=4, accel_type=None, accel_count=0)
            ),
        ),
        Desc(
            mock,
            metadata=Metadata(
                resources=Resources(cpus=4, memory=8, accel_type="A100", accel_count=1)
            ),
        ),
        Desc(
            mock,
            metadata=Metadata(
                resources=Resources(cpus=1, memory=2, accel_type=None, accel_count=0)
            ),
        ),
    ]


def test_place_all_local(tasks):
    nodes = [
        Node(
            name="local",
            executor="",
            cpus=8,
            memory=16,
            accel_type="A100",
            accel_count=1,
        ),  # orchestrator here maybe
        Node(
            name="gpu_k8s",
            executor="",
            cpus=32,
            memory=128,
            accel_type="A100",
            accel_count=6,
        ),
        Node(
            name="gpu_2",
            executor="",
            cpus=16,
            memory=64,
            accel_type="A100",
            accel_count=2,
        ),
    ]
    assignment_result = assignment(tasks, nodes, local_index=0, time_limit_s=10.0)
    assert assignment_result == {0: 0, 1: 0, 2: 0}


def test_place_mixed(tasks):
    nodes = [
        Node(
            name="local",
            executor="",
            cpus=4,
            memory=8,
            accel_type="A100",
            accel_count=1,
        ),  # orchestrator here maybe
        Node(
            name="gpu_k8s",
            executor="",
            cpus=32,
            memory=128,
            accel_type="A100",
            accel_count=6,
        ),
        Node(
            name="gpu_2",
            executor="",
            cpus=16,
            memory=64,
            accel_type="A100",
            accel_count=2,
        ),
    ]
    assignment_result = assignment(tasks, nodes, local_index=0, time_limit_s=10.0)
    assert assignment_result == {0: 0, 1: 1, 2: 0}


def test_place_less_nodes(tasks):
    nodes = [
        Node(
            name="local",
            executor="",
            cpus=2,
            memory=2,
            accel_type="A100",
            accel_count=0,
        ),  # orchestrator here maybe
        Node(
            name="gpu_k8s",
            executor="",
            cpus=32,
            memory=128,
            accel_type="A100",
            accel_count=6,
        ),
        Node(
            name="gpu_2",
            executor="",
            cpus=16,
            memory=64,
            accel_type="A100",
            accel_count=2,
        ),
    ]
    assignment_result = assignment(tasks, nodes, local_index=0, time_limit_s=10.0)
    assert assignment_result == {0: 2, 1: 2, 2: 0}
