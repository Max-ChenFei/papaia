import ast
import asyncio
from typing import Dict, Tuple

from ortools.sat.python import cp_model

from .executors import get_executor_by_name, Executor
from ..IR import Desc, available_nodes, Node


def print_assignment(
    plan: dict[int, int], nodes: list[Node], tasks: list[Desc]
) -> None:
    """Print the assignment plan for debugging."""
    for task_idx, node_idx in plan.items():
        task = tasks[task_idx]
        node = nodes[node_idx]
        print(f"Tool '{task.ast_node.name}' assigned to Node '{node.name}' ")


async def place_on_exec_sites(
    descs: dict[str, Desc], nodes_path: str
) -> tuple[dict[str, ast.AST], dict[str, Executor]]:
    """Place on available execution nodes and return access stub and used executors."""
    exec_nodes, local_index = available_nodes(nodes_path)
    plan = assignment(list(descs.values()), exec_nodes, local_index=local_index)

    print_assignment(plan, exec_nodes, list(descs.values()))

    stub_ast = {}
    executors = {}
    names = list(descs.keys())
    values = list(descs.values())

    # Prepare tasks for parallel execution
    tasks = []
    for i, node_index in plan.items():
        name = names[i]
        desc = values[i]
        node = exec_nodes[node_index]
        desc.assigned_node = node
        desc.assigned_accel_devices = node.get_accel_devices(desc.resources.accel_count)
        executor_instance = get_executor_by_name(
            node.executor, desc.pip_install is not None
        )
        tasks.append((name, executor_instance, node, desc))

    # Execute all tasks in parallel
    results = await asyncio.gather(
        *(executor.run(node, desc) for _, executor, node, desc in tasks)
    )

    # Collect results
    for (name, executor, _, _), result in zip(tasks, results):
        stub_ast[name] = result
        executors[name] = executor

    return stub_ast, executors


def assignment(
    tasks: list[Desc],
    nodes: list[Node],
    local_index: int | None = None,
    time_limit_s: float = 10.0,
    num_workers: int = 8,
) -> dict[int, int]:
    """Assign tasks to execution nodes using CP-SAT solver.
    returns a mapping from task index to node index.
    """
    model = cp_model.CpModel()

    I = range(len(tasks))
    J = range(len(nodes))
    J_i: list = candidate_nodes(tasks, nodes)

    # Variables: only create x[i,j] for j in J_i[i]
    x: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for i in I:
        for j in J_i[i]:
            x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")
    y: Dict[int, cp_model.IntVar] = {j: model.NewBoolVar(f"y_{j}") for j in J}

    # Constraint (1) Unique assignment: exactly one node per task
    for i in I:
        model.Add(sum(x[(i, j)] for j in J_i[i]) == 1)

    # Constraint (3) Resource capacities per node
    for j in J:
        assigned_x = [(i, x[(i, j)]) for i in I if (i, j) in x]
        if not assigned_x:
            continue

        model.Add(
            sum(tasks[i].resources.cpus * var for i, var in assigned_x) <= nodes[j].cpus
        )
        model.Add(
            sum(tasks[i].resources.memory * var for i, var in assigned_x)
            <= nodes[j].memory
        )

        # Accelerator capacity (same type on node, so just total count)
        model.Add(
            sum(tasks[i].resources.accel_count * var for i, var in assigned_x)
            <= nodes[j].accel_count
        )

    # Constraint (4) Link x and y: if any task assigned to node j, then y[j] = 1
    for (i, j), var in x.items():
        model.Add(var <= y[j])

    # Objective components
    def c(j: int) -> int:
        if local_index is None:
            return 1
        return 0 if j == local_index else 1

    R = sum(c(j) * x[(i, j)] for i in I for j in J_i[i])  # remote tasks
    S = sum(y[j] for j in J)  # nodes used

    M = len(nodes) + 1
    model.Minimize(M * R + S)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = (
        time_limit_s  # e.g., 10s :contentReference[oaicite:4]{index=4}
    )
    solver.parameters.num_search_workers = num_workers
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"No solution found. Solver status: {solver.StatusName(status)}"
        )

    assignment: Dict[int, int] = {}
    for i in I:
        for j in J_i[i]:
            if solver.Value(x[(i, j)]) == 1:
                assignment[i] = j
                break
    return assignment


def candidate_nodes(tasks: list, nodes: list[Node]) -> list[list[int]]:
    """Build J_i by filtering infeasible task-node pairs."""
    if not nodes:
        raise ValueError("No available execution nodes to assign tasks to.")
    J_i: list[list[int]] = []
    for t in tasks:
        r = t.resources
        cand = []
        for j, n in enumerate(nodes):
            # Accelerator compatibility
            if r.accel_count == 0 or r.accel_type is None:
                # task doesn't require accel; any node ok
                if n.cpus is not None:
                    if n.cpus >= r.cpus and n.memory >= r.memory:
                        cand.append(j)
            else:
                if (
                    n.accel_type == r.accel_type
                    and n.accel_count >= r.accel_count
                    and n.cpus >= r.cpus
                    and n.memory >= r.memory
                ):
                    cand.append(j)

        if not cand:
            available = "\n".join(str(node) for node in nodes)
            raise ValueError(
                f"No feasible node for {t.ast_node.name} with {r}.\nCurrent available nodes: \n{available}"
            )
        J_i.append(cand)
    return J_i
