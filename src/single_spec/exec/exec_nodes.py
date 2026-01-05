import tomllib
from pathlib import Path

from .exec_node import ExecNode
from ..IR.resources import Resources


EXEC_NODE_CONFIG_FILENAME = "exec_nodes.toml"


def available_exec_nodes() -> tuple[str | None, list[ExecNode]]:
    path = Path(EXEC_NODE_CONFIG_FILENAME)
    if not path.exists():
        Warning(
            "No exec_nodes.toml found in current working directory, proceeding with no available exec nodes."
        )
        return None, []
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    default_node = data.get("default")
    if default_node is not None and not isinstance(default_node, str):
        raise ValueError("default_node must be a string if provided.")

    nodes_tbl = data.get("nodes")
    if not isinstance(nodes_tbl, dict):
        raise ValueError(
            "exec_sites.toml must contain a [nodes] table with sub-tables like [nodes.local]."
        )

    nodes = []
    for name, cfg in nodes_tbl.items():
        if not isinstance(cfg, dict):
            raise ValueError(f"[nodes.{name}] must be a table.")

        resources = Resources(
            cpus=cfg.get("cpus"), memory=cfg.get("memory"), accel=cfg.get("accel")
        )
        nodes.append(ExecNode(name=name, resources=resources))

    if default_node is not None and default_node not in {s.name for s in nodes}:
        raise ValueError(
            f"default_site='{default_node}' not found among nodes: {[s.name for s in nodes]}"
        )

    return default_node, nodes
