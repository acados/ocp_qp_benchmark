"""Benchmark runner."""

from time import perf_counter

import numpy as np
from tqdm import tqdm

from acados_template import AcadosOcpQp, AcadosOcpQpSolver, AcadosOcpQpOptions

from ocp_qp_benchmark.core.test_set import TestSet
from ocp_qp_benchmark.core.solver_set import SolverSet
from ocp_qp_benchmark.core.results import Results


def solve_problem(
    qp: AcadosOcpQp,
    solver: str,
    solver_settings,
    repeat_times: int = 1,
    print_level: int = 0,
) -> dict:
    """Solve a single QP problem with the given solver.

    Args:
        qp: The OCP QP problem to solve.
        solver: Name of the solver to use.
        solver_settings: Solver settings (currently unused, for future extension).
        repeat_times: Number of times to repeat the solve (for timing).
        print_level: Verbosity level.

    Returns:
        Dictionary containing solve results (status, iterations, runtimes, cost).
    """
    ctx = {}
    runtime_external = 1e50

    if repeat_times != 1:
        raise NotImplementedError("repeat_times != 1 not implemented yet")

    for _ in range(repeat_times):
        opts = AcadosOcpQpOptions()
        opts.qp_solver = solver
        opts.print_level = print_level - 1
        opts.iter_max = 1000
        try:
            qp_solver = AcadosOcpQpSolver(qp, opts)
        except Exception as e:
            if print_level > 0:
                print(f"Error initializing solver {solver} got error:\n {e}")
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
            print(f"Solver {solver} failed with status {status}")
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
        nb_solvers = len(solver_set.solvers)
        nb_settings = len(solver_set.solver_settings)
        progress_bar = tqdm(
            total=nb_problems * nb_solvers * nb_settings,
            initial=0,
        )

    for solver in solver_set.solvers:
        # setting is not really used here, but kept for future extension
        for solver_settings in solver_set.solver_settings:
            progress_bar.set_description(
                f"Solver: {solver}, Setting: {solver_settings}"
            )
            for json_path_dict in test_set:
                qp = AcadosOcpQp.from_json(json_path_dict["qp_data_path"])
                if print_level > 1:
                    print(
                        f"Solving problem {json_path_dict['qp_data_path']} "
                        f"with solver {solver} and settings {solver_settings}"
                    )
                ctx = solve_problem(
                    qp, solver, solver_settings, print_level=print_level - 1
                )
                results.update(
                    json_path_dict["meta_data_path"],
                    solver,
                    solver_settings,
                    ctx,
                )
                if progress_bar is not None:
                    progress_bar.update(1)
        results.write()

    if progress_bar is not None:
        progress_bar.close()
