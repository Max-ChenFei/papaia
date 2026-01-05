def required(env: str | None = None, accel: str | None = None):
    """Decorator to annotate runtime metadata for a function.

    Args:
        env: Runtime environment string (e.g., "python:3.10").
        accel: Accelerator requirement. Format: "<name>:<count>" or "<name>"
            (defaults to a count of 1). Example: "H100:4".

    Returns:
        A decorator that returns the original function (metadata annotation only).
    """

    def decorator(func):
        return func

    return decorator


def required_cls(
    entry: str,
    env: str | None = None,
    accel: str | None = None,
    setup: str | None = None,
    teardown: str | None = None,
):
    """Decorator to annotate runtime metadata for a class.

    Args:
        entry: Entry method name for the class.
        env: Runtime environment string (e.g., "python:3.10").
        accel: Accelerator requirement. Format: "<name>:<count>" or "<name>"
            (defaults to a count of 1). Example: "H100:4".
        setup: Setup method name for the class.
        teardown: Teardown method name for the class.

    Returns:
        A decorator that returns the original class (metadata annotation only).
    """

    def decorator(cls):
        return cls

    return decorator


decorator_keywords = [required.__name__, required_cls.__name__]
