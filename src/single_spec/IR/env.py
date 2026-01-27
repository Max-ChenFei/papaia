# container_image or (container_image, pip_packages) e.g., ("python:3.10-slim", ["fastapi", "uvicorn"])
Env = str | tuple[str | None, list[str] | None]
