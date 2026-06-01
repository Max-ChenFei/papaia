# path to requirements.txt e.g., "requirements.txt"
# list of pip packages e.g., ["fastapi", "uvicorn"]
PipInstall = str | list[str]


def merge_pip_install(
    existing: PipInstall | None, new: list[str]
) -> str | list[str] | tuple:
    if existing is None:
        return new
    if isinstance(existing, list):
        existing.extend(new)
        return existing
    if isinstance(existing, tuple):
        return existing + (new,)
    return (existing, new)
