import inspect

from .metadata import Metadata
from .registry import register
from .runtime_env import Env


def required_fn(
    env: Env | None = None,
    gpu: int | None = None,  # GPU requirement as a string (e.g., "2xA100").
):
    "decorator to annotate metadata for a function"

    def decorator(func):
        if not inspect.isfunction(func):
            raise ValueError("@required_fn can only be applied to functions.")
        register(func, Metadata(env=env, gpu=gpu, entry=func.__name__))
        return func

    return decorator


def required_cls(
    entry: str,  # cls: method name
    env: Env | None = None,
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
            Metadata(env=env, gpu=gpu, entry=entry, setup=setup, teardown=teardown),
        )
        return cls

    return decorator
