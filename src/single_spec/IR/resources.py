from dataclasses import dataclass, fields


@dataclass
class Resources:
    """Resource requirements specification.

    Attributes:
        cpus: Number of CPUs at least.
        memory: Memory specification in GB at least.
        accel: Accelerator requirement. Format: "<name>:<count>" or "<name>"
            (defaults to a count of 1). Example: "H100:4".
    """

    cpus: int | None = None
    memory: int | None = None
    accel: str | None = None


RESOURCE_FIELDS = {f.name for f in fields(Resources)}
