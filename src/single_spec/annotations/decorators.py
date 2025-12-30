import inspect

from .metadata import Metadata
from .registry import register
from .docker_image import Image


def required_fn(
    image: Image | None = None,
    gpu: int | None = None,  # GPU requirement as a string (e.g., "2xA100").
):
    "decorator to annotate metadata for a function"

    def decorator(func):
        if not inspect.isfunction(func):
            raise ValueError("@required_fn can only be applied to functions.")
        register(func, Metadata(image=image, gpu=gpu, entry=func.__name__))
        return func

    return decorator


def required_cls(
    entry: str,  # cls: method name
    image: Image | None = None,
    gpu: int | None = None,  # GPU requirement as a string (e.g., "2xA100").
    setup: str = "__init__",  # class only; ignored for functions
    teardown: str | None = None,  # class only; ignored for functions
):
    "decorator to annotate metadata for a class"

    def decorator(cls):
        if not inspect.isclass(cls):
            raise ValueError("@required_cls can only be applied to classes.")
        register(
            cls,
            Metadata(image=image, gpu=gpu, entry=entry, setup=setup, teardown=teardown),
        )
        return cls

    return decorator
