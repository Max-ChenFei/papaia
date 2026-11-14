from .executor import Executor
from .current_process import CurrentProcess
from .another_process import AnotherProcess
from .remote_venv import RemoteVenv
from .venv import VenvExecutor

available_executors = {
    "local_same_process": CurrentProcess(),
    "local_venv": VenvExecutor(),
    "remote": RemoteVenv(),
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


def stop_all() -> None:
    """Stop every service started by the built-in executors (used when deployment fails)."""
    for executor in available_executors.values():
        for name in list(getattr(executor, "_processes", {})):
            try:
                executor.stop(name)
            except Exception as e:  # keep stopping the others
                print(f"Error stopping tool '{name}': {e}", flush=True)
