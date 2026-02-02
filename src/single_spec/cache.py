import json
from pathlib import Path
import shutil
import asyncssh
import asyncio
from .IR.nodes import Node

CACHE_DIR: str = ".single_spec_cache"

LOCAL_CACHE_DIR: Path = Path(CACHE_DIR).resolve()
REMOTE_CACHE_DIR: str = f"/tmp/{CACHE_DIR}"

REMOTE_CACHE: list[(Node, str)] = []

if not LOCAL_CACHE_DIR.exists():
    LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def add_remote_cache(node: Node, remote_dir: str) -> None:
    REMOTE_CACHE.append((node, remote_dir))


def save_remote_cache_config() -> None:
    obj = [
        {
            "node_name": node.name,
            "remote_dir": remote_dir,
            "host": node.host,
            "port": node.port,
            "username": node.username,
            "password": node.password,
        }
        for node, remote_dir in REMOTE_CACHE
    ]
    json.dump(obj, open(LOCAL_CACHE_DIR / "remote_cache.json", "w"), indent=4)


def clear_cache() -> None:
    asyncio.run(clear_remote_cache())
    clear_local_cache()


async def clear_remote_cache() -> None:
    remote_cache = (
        json.loads((LOCAL_CACHE_DIR / "remote_cache.json").read_text())
        if (LOCAL_CACHE_DIR / "remote_cache.json").exists()
        else []
    )

    for cache in remote_cache:
        async with asyncssh.connect(
            host=cache["host"],
            port=cache["port"],
            username=cache["username"],
            password=cache["password"],
        ) as conn:
            try:
                await conn.run(f"rm -rf {cache['remote_dir']}")
            except Exception:
                pass


def clear_local_cache() -> None:
    shutil.rmtree(LOCAL_CACHE_DIR, ignore_errors=True)
