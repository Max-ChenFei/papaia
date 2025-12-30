from typing import List, TypeAlias

Image: TypeAlias = str  # Docker image reference (e.g., "python:3.12-slim") used for pulling from Docker Hub.


class Dockerfile:
    """
    Class representing a Docker image configuration.

    Provides a fluent interface for building Docker image specifications
    by chaining pip packages and shell commands.

    Attributes:
        base_image: The base Docker image to build from.
        packages: List of Python packages to install via pip.
        commands: List of shell commands to run during image build.
    """

    def __init__(self):
        self.base_image: str = "python:3.10-slim"
        self.packages: List[str] = []
        self.commands: List[str] = []

    def pip_install(self, *packages: str) -> "Dockerfile":
        self.packages.extend(packages)
        return self

    def run(self, command: str) -> "Dockerfile":
        self.commands.append(command)
        return self

    def __repr__(self):
        """Return string representation of the Docker image configuration."""
        return f"Dockerfile(base_image={self.base_image!r}, packages={self.packages!r}, commands={self.commands!r})"

    def to_dockerfile(self) -> str:
        dockerfile = [f"FROM {self.base_image}"]
        if self.packages:
            dockerfile.append(f"RUN pip install {' '.join(self.packages)}")
        for cmd in self.commands:
            dockerfile.append(f"RUN {cmd}")
        return "\n".join(dockerfile)


Env = Image | Dockerfile
