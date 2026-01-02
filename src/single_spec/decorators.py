def required(
    env: str | None = None,
    gpu: int | None = None,  # GPU requirement as a string (e.g., "2xA100").
):
    "decorator to annotate metadata for a function"

    def decorator(func):
        return func

    return decorator


def required_cls(
    entry: str,  # cls: method name
    env: str | None = None,
    gpu: int | None = None,  # GPU requirement as a string (e.g., "2xA100").
    setup: str | None = None,  # class only; ignored for functions
    teardown: str | None = None,  # class only; ignored for functions
):
    "decorator to annotate metadata for a class"

    def decorator(cls):
        return cls

    return decorator


decorator_keywords = [required.__name__, required_cls.__name__]
