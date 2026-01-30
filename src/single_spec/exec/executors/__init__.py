from .executor import Executor
from .current_process import CurrentProcess
from .another_process import AnotherProcess
from .venv import VenvExecutor

available_executors = {
    "local_same_process": CurrentProcess(),
    "local_venv": VenvExecutor(),
}


def get_executor_by_name(name: str, addition_env: bool = True) -> Executor:
    if name == "local":
        name = "local_venv" if addition_env else "local_same_process"
    executor = available_executors.get(name)
    if executor is None:
        raise ValueError(f"Executor '{name}' is not available.")
    return executor


def add_executor(name: str, executor: Executor) -> None:
    if name in available_executors:
        raise ValueError(f"Executor '{name}' already exists.")
    available_executors[name] = executor
