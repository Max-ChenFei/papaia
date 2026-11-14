import os

from papaia.accel_assign import (
    assign_accel_devices_code,
    assigned_accel_devices,
)


def test_assign_accel_code():
    code = assign_accel_devices_code("my_tool", "0,1")
    expected_code = """import os
os.environ["TOOL_ACCEL_INDEXES__my_tool"] = "0,1"
"""
    assert code == expected_code


def test_get_assigned_accel():
    os.environ["TOOL_ACCEL_INDEXES__my_tool"] = "0,1"
    indexes = assigned_accel_devices("my_tool")
    assert indexes == "0,1"


def test_assigned_device(monkeypatch):
    from papaia import assigned_device
    from papaia.accel_assign import PREFIX

    monkeypatch.delenv(f"{PREFIX}dev_tool", raising=False)
    assert assigned_device("dev_tool") == "cpu"  # no accelerator assigned
    monkeypatch.setenv(f"{PREFIX}dev_tool", "2")
    assert assigned_device("dev_tool") == "cuda:2"
    monkeypatch.setenv(f"{PREFIX}dev_tool", "0,1")
    assert assigned_device("dev_tool") == "cuda:0"  # first of several devices
