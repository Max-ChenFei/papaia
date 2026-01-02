import ast

from .backends import get_backend_by_name, ExecutionBackend
from .available_exec_sites import available_exec_sites

from .exec_site import ExecSite
from ..IR import Desc


def place_on_exec_sites(
    descs: dict[str, Desc],
) -> tuple[dict[str, ast.AST], dict[str, ExecutionBackend]]:
    """Place tools on available execution sites and return access stub and used backends."""
    # Todo: retrieve latest exec sites and its capabilities
    default_site_name, exec_sites = available_exec_sites()
    plan = plan_placement(descs, exec_sites, default_site_name)

    stub_ast = {}
    backend = {}
    for tool_name, site in plan.items():
        backend_instance = get_backend_by_name(site.name)
        stub_ast[tool_name] = backend_instance.run(descs[tool_name])
        backend[tool_name] = backend_instance
    return stub_ast, backend


def plan_placement(
    descs: dict[str, Desc], exec_sites: list[ExecSite], default_site_name: str | None
) -> dict[str, ExecSite]:
    placement: dict[str, ExecSite] = {}

    # Todo: simple placement logic: assign tools to exec sites based on required capabilities

    return placement
