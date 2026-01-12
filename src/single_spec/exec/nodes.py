import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Node:
    name: str
    backend: str
    cpus: int | None = 0
    memory: int | None = 0
    accel_type: str | None = None
    accel_count: int | None = 0


EXEC_NODE_CONFIG_FILENAME = "exec_nodes.toml"


def available_nodes() -> tuple[list[Node], int | None]:
    path = Path(EXEC_NODE_CONFIG_FILENAME)
    if not path.exists():
        Warning(
            "No exec_nodes.toml found in current working directory, proceeding with no available exec nodes."
        )
        return [], None
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    nodes_tbl = data.get("nodes")
    if not isinstance(nodes_tbl, dict):
        raise ValueError(
            "exec_sites.toml must contain a [nodes] table with sub-tables like [nodes.local]."
        )
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
                backend=cfg.get("backend"),
                cpus=cfg.get("cpus"),
                memory=cfg.get("memory"),
                accel_type=accel_type,
                accel_count=accel_count,
            )
        )
        if name == "local":
            local_index = len(nodes) - 1

    return nodes, local_index
