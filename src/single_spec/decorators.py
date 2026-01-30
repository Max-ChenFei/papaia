def required(
    pip_install: str | list[str] | None = None,
    cpus: int | None = None,
    memory: int | None = None,
    accel: str | None = None,
):
    """Decorator to annotate runtime metadata for a function.

    Args:
        pip_install: Pip install specifications. Can be:
            - str: path to requirements.txt
            - list[str]: list of pip packages
        cpus: Number of CPUs at least.
        memory: Memory specification in GB at least.
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
    cpus: int | None = None,
    memory: int | None = None,
    pip_install: str | list[str] | None = None,
    accel: str | None = None,
    setup: str | None = None,
    teardown: str | None = None,
):
    """Decorator to annotate runtime metadata for a class.

    Args:
        entry: Entry method name for the class.
        cpus: Number of CPUs at least.
        memory: Memory specification in GB at least.
        pip_install: Pip install specifications. Can be:
            - str: path to requirements.txt
            - list[str]: list of pip packages
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
