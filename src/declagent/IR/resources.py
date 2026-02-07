from dataclasses import dataclass, fields


@dataclass
class Resources:
    """Resource requirements specification.

    Attributes:
        cpus: Number of CPUs at least.
        memory: Memory specification in GB at least.
        accel_type: Accelerator name like "A100".
        accel_count: Number of accelerators at least.
    """

    cpus: int = 0
    memory: int = 0
    accel_type: str | None = None
    accel_count: int = 0


RESOURCE_FIELDS = {f.name for f in fields(Resources)}
