from .executor import Executor
from .current_process import CurrentProcess
from .another_process import AnotherProcess

available_executors = {
    "local_same_process": CurrentProcess(),
}


def get_executor_by_name(name: str, addition_env: bool = True) -> Executor:
    executor = available_executors.get(name)
    if executor is None:
        raise ValueError(f"Executor '{name}' is not available.")
    return executor


def add_executor(name: str, executor: Executor) -> None:
    if name in available_executors:
        raise ValueError(f"Executor '{name}' already exists.")
    available_executors[name] = executor
