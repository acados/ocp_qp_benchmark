"""Benchmark runner."""

from copy import deepcopy
from time import perf_counter

import numpy as np
from tqdm import tqdm

from acados_template import AcadosOcpQp, AcadosOcpQpSolver, AcadosOcpQpOptions

from ocp_qp_benchmark.core.test_set import TestSet
from ocp_qp_benchmark.core.solver_set import SolverSet, get_solver_id
from ocp_qp_benchmark.core.results import Results


def solve_problem(
    qp: AcadosOcpQp,
    opts: AcadosOcpQpOptions,
    repeat_times: int = 1,
    print_level: int = 0,
) -> dict:
    """Solve a single QP problem with the given solver options.

    Args:
        qp: The OCP QP problem to solve.
        opts: Solver options (will be copied to avoid mutation).
        repeat_times: Number of times to repeat the solve (for timing).
        print_level: Verbosity level (overrides opts.print_level).

    Returns:
        Dictionary containing solve results (status, iterations, runtimes, cost).
    """
    ctx = {}
    runtime_external = 1e50

    if repeat_times != 1:
        raise NotImplementedError("repeat_times != 1 not implemented yet")

    # Copy options to avoid mutation and set print level
    solver_opts = deepcopy(opts)
    solver_opts.print_level = print_level - 1

    for _ in range(repeat_times):
        try:
            qp_solver = AcadosOcpQpSolver(qp, solver_opts)
        except Exception as e:
            if print_level > 0:
                print(
                    f"Error initializing solver {opts.qp_solver} "
                    f"got error:\n {e}"
                )
            ctx["status"] = -1  # ACADOS_UNKNOWN
            ctx["iterations"] = -1
            ctx["runtime_external"] = -1
            ctx["runtime_internal"] = -1
            ctx["runtime_fair"] = -1
            ctx["cost"] = np.nan
            return ctx

        start_time = perf_counter()
        status = qp_solver.solve()
        if print_level > 0 and status != 0:
            print(f"Solver {opts.qp_solver} failed with status {status}")
        runtime_external = min(runtime_external, perf_counter() - start_time)
        iter = qp_solver.get_stats("iter")
        runtime_internal = qp_solver.get_stats("time_tot")
        runtime_fair = (
            qp_solver.get_stats("time_qp_xcond")
            + qp_solver.get_stats("time_qp_solver_call")
        )
        # TODO: reset() needed
        qp_solver = None

    ctx["status"] = status
    ctx["iterations"] = iter
    ctx["runtime_external"] = runtime_external
    ctx["runtime_internal"] = runtime_internal
    ctx["runtime_fair"] = runtime_fair
    # TODO: get_cost() needs to be called after solve()
    ctx["cost"] = 0.0

    return ctx


def run(
    test_set: TestSet,
    solver_set: SolverSet,
    results: Results,
    print_level: int = 1,
) -> None:
    """Run a given test set and store results.

    Args:
        test_set: The test set containing problems to benchmark.
        solver_set: The set of solvers to benchmark.
        results: Results object to store benchmark results.
        print_level: Verbosity level.
    """
    progress_bar = None
    if print_level > 0:
        nb_problems = test_set.count_problems()
        nb_solvers = len(solver_set)
        progress_bar = tqdm(
            total=nb_problems * nb_solvers,
            initial=0,
        )

    for opts in solver_set:
        solver_id = get_solver_id(opts)
        if progress_bar is not None:
            progress_bar.set_description(f"Solver: {solver_id}")

        for json_path_dict in test_set:
            qp = AcadosOcpQp.from_json(json_path_dict["qp_data_path"])
            if print_level > 1:
                print(
                    f"Solving problem {json_path_dict['qp_data_path']} "
                    f"with solver {solver_id}"
                )
            ctx = solve_problem(qp, opts, print_level=print_level - 1)
            results.update(
                json_path_dict["meta_data_path"],
                solver_id,
                ctx,
            )
            if progress_bar is not None:
                progress_bar.update(1)

        results.write()

    if progress_bar is not None:
        progress_bar.close()
