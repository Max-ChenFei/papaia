from pathlib import Path
import shutil

CACHE_PATH: Path = Path(".single_spec_cache").resolve()
if not CACHE_PATH.exists():
    CACHE_PATH.mkdir(parents=True, exist_ok=True)


def clear_cache() -> None:
    """Clears the entire cache directory."""
    shutil.rmtree(CACHE_PATH, ignore_errors=True)
