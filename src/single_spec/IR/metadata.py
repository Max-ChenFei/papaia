import ast
from dataclasses import dataclass

from .pip_install import Pip_Install
from .resources import RESOURCE_FIELDS, Resources


@dataclass(frozen=True)
class Metadata:
    """Runtime metadata for a function or class.

    Attributes:
        pip_install: Pip install specifications (e.g., requirements.txt path or list of packages).
        resources: Resource requirements (cpus, memory, accel).
        entry: Entry method name for the class.
        setup: Setup method name for the class.
        teardown: Teardown method name for the class.
    """

    pip_install: Pip_Install | None = None
    resources: Resources | None = None

    entry: str | None = None
    setup: str | None = None
    teardown: str | None = None


def extract_metadata(decorator: ast.Call, is_class_def: bool) -> Metadata | None:
    metadata_kwargs = {}
    resource_kwargs = {}

    for keyword in decorator.keywords:
        value = ast.literal_eval(keyword.value)
        if keyword.arg in RESOURCE_FIELDS or keyword.arg == "accel":
            if keyword.arg == "accel" and value is not None:
                if ":" in value:
                    accel_name, accel_count_str = value.split(":", 1)
                    resource_kwargs["accel_type"] = accel_name
                    resource_kwargs["accel_count"] = int(accel_count_str)
                else:
                    resource_kwargs["accel_type"] = value
                    resource_kwargs["accel_count"] = 1
            else:
                resource_kwargs[keyword.arg] = value
        else:
            metadata_kwargs[keyword.arg] = value

    if not metadata_kwargs and not resource_kwargs:
        return None

    if is_class_def and (
        "entry" not in metadata_kwargs or metadata_kwargs["entry"] is None
    ):
        raise ValueError("Class metadata must specify 'entry' method.")

    resources = Resources(**resource_kwargs)
    return Metadata(resources=resources, **metadata_kwargs)
