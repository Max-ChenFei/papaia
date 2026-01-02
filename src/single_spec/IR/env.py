from typing import TypeAlias

Image: TypeAlias = str  # Docker image reference (e.g., "python:3.12-slim") used for pulling from Docker Hub.


Env = Image  # Todo: add more environment types later
