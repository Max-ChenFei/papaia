import tomllib
from pathlib import Path


class Node:
    def __init__(
        self,
        name: str,
        executor: str,
        cpus: int | None = None,
        memory: int | None = None,
        accel_type: str | None = None,
        accel_count: int | None = None,
    ):
        self.name = name
        self.executor = executor
        self.cpus = cpus
        self.memory = memory
        self.accel_type = accel_type
        self.accel_count = accel_count  # id from 0 to N-1

        self.accel_assignment: dict[str, list] = {}  # e.g., {"task1": [0,1]}
        self.accel_assigned = [False] * (accel_count or 0)

    def __str__(self):
        return (
            f"Node(name={self.name}, executor={self.executor}, cpus={self.cpus}, "
            f"memory={self.memory}, accel_type={self.accel_type}, "
            f"accel_count={self.accel_count})"
        )

    def get_accel_devices(self, count) -> str | None:
        if (
            self.accel_type is None
            or self.accel_count is None
            or self.accel_count == 0
            or count > self.accel_count
        ):
            return None
        devices = []
        for i in range(self.accel_count):
            if not self.accel_assigned[i]:
                devices.append(str(i))
                self.accel_assigned[i] = True
            if len(devices) >= count:
                break
        if len(devices) < count:
            raise RuntimeError(
                f"Not enough available accelerators on node {self.name}."
            )

        return ",".join(devices)

    def release_accel_devices(self, devices: str) -> None:
        for dev in devices.split(","):
            idx = int(dev)
            self.accel_assigned[idx] = False


EXEC_NODE_CONFIG_FILENAME = "exec_nodes.toml"


def available_nodes() -> tuple[list[Node], int | None]:
    path = Path(EXEC_NODE_CONFIG_FILENAME)
    if not path.exists():
        raise FileNotFoundError(
            f"No exec_nodes.toml found in current working directory ({path.resolve()})."
        )
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    nodes_tbl = data.get("nodes")
    if not isinstance(nodes_tbl, dict):
        raise ValueError(
            "exec_sites.toml must contain a [nodes] table with sub-tables like [nodes.local]."
        )
    if len(nodes_tbl.items()) == 0:
        raise ValueError("exec_sites.toml must contain at least one node in [nodes].")
    nodes = []
    local_index = None
    for name, cfg in nodes_tbl.items():
        accel = cfg.get("accel")
        accel_type = (
            None if accel is None else accel.split(":")[0] if ":" in accel else accel
        )
        accel_count = (
            None if accel is None else int(accel.split(":")[-1]) if ":" in accel else 1
        )
        nodes.append(
            Node(
                name=name,
                executor=cfg.get("executor"),
                cpus=cfg.get("cpus"),
                memory=cfg.get("memory"),
                accel_type=accel_type,
                accel_count=accel_count,
            )
        )
        if name == "local":
            local_index = len(nodes) - 1
    if len(nodes) == 0:
        raise ValueError("No execution nodes defined in exec_nodes.toml.")
    if local_index is None:
        raise ValueError("exec_nodes.toml must define a 'local' node.")
    return nodes, local_index
