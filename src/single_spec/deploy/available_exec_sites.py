import tomllib
from pathlib import Path

from .exec_site import ExecSite


EXECSITE_CONFIG_FILENAME = "exec_sites.toml"


def available_exec_sites() -> tuple[str | None, list[ExecSite]]:
    path = Path(EXECSITE_CONFIG_FILENAME)
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    default_site = data.get("default")
    if default_site is not None and not isinstance(default_site, str):
        raise ValueError("default_site must be a string if provided.")

    sites_tbl = data.get("sites")
    if not isinstance(sites_tbl, dict):
        raise ValueError(
            "exec_sites.toml must contain a [sites] table with sub-tables like [sites.local]."
        )

    sites = []
    for name, cfg in sites_tbl.items():
        if not isinstance(cfg, dict):
            raise ValueError(f"[sites.{name}] must be a table.")

        sites.append(ExecSite(name=name, capabilities=cfg))

    if default_site is not None and default_site not in {s.name for s in sites}:
        raise ValueError(
            f"default_site='{default_site}' not found among sites: {[s.name for s in sites]}"
        )

    return default_site, sites
