"""Benchmark runner."""

import json
import os
from copy import deepcopy
from time import perf_counter

import numpy as np
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from typing import Optional, Union
import logging

from acados_template import AcadosOcpQp, AcadosOcpQpSolver, AcadosCasadiOcpQpSolver, AcadosOcpQpOptions, AcadosOcpIterate

from ocp_qp_benchmark.core.test_set import TestSet
from ocp_qp_benchmark.core.solver_set import SolverSet
from ocp_qp_benchmark.core.results import Results
from ocp_qp_benchmark.core.external import ExternalSolverConfig
from ocp_qp_benchmark.utils.io import decompress
from ocp_qp_benchmark.core.supported_solvers import (
    ACADOS_OCP_QP_SOLVERS,
    ACADOS_CASADI_SOLVERS,
)


def solve_problem(
    qp: AcadosOcpQp,
    opts: Union[AcadosOcpQpOptions, dict, ExternalSolverConfig],
    repeat_times: int = 1,
) -> tuple[dict, Optional[AcadosOcpIterate]]:
    """Solve a single QP problem with the given solver options.

    Args:
        qp: The OCP QP problem to solve.
        opts: Solver options (will be copied to avoid mutation).
        repeat_times: Number of times to repeat the solve (for timing).
        print_level: Verbosity level (overrides opts.print_level).

    Returns:
        Dictionary containing solve results (status, iterations, runtimes, cost),
        and the solution iterate (None if unavailable).
    """
    if not isinstance(opts, (AcadosOcpQpOptions, dict, ExternalSolverConfig)):
        raise ValueError('Unknown solver options type, expected AcadosOcpQpOptions, dict or ExternalSolverConfig')

    ctx = {}
    runtime_external = 1e50

    if repeat_times != 1:
        raise NotImplementedError("repeat_times != 1 not implemented yet")

    # Copy options to avoid mutation and set print level
    solver_opts = deepcopy(opts)
    # solver_opts.print_level = print_level - 1
    if isinstance(solver_opts, ExternalSolverConfig):
        solver_name = solver_opts.name
    else:
        solver_name = solver_opts.get('qp_solver')

    for _ in range(repeat_times):
        try:
            if solver_name in ACADOS_OCP_QP_SOLVERS:
                qp_solver = AcadosOcpQpSolver(qp, solver_opts)
            elif solver_name in ACADOS_CASADI_SOLVERS:
                casadi_opts = solver_opts.copy()
                casadi_opts.pop('qp_solver')
                qp_solver = AcadosCasadiOcpQpSolver(qp,
                                                    solver=solver_name.lower(),
                                                    solver_opts=casadi_opts)
            elif isinstance(solver_opts, ExternalSolverConfig):
                ext_qp = solver_opts.qp_cls.from_acados_qp(qp)
                qp_solver = solver_opts.solver_cls(ext_qp, solver_opts.opts)
            else:
                raise ValueError(f"Unknown solver: {solver_name}")
        except Exception as e:
            logging.error(f"Error initializing solver {solver_name} got error:\n {e}")
            ctx["status"] = -1  # ACADOS_UNKNOWN
            ctx["iterations"] = -1
            ctx["runtime_external"] = -1
            ctx["runtime_internal"] = -1
            ctx["runtime_fair"] = -1
            ctx["cost"] = np.nan
            return ctx, None

        start_time = perf_counter()
        status = qp_solver.solve()
        if status != 0:
            logging.warning(f"Solver {solver_name} failed with status {status}")

        runtime_external = min(runtime_external, perf_counter() - start_time)
        iter = qp_solver.get_stats("iter")
        runtime_internal = qp_solver.get_stats("time_tot")
        if solver_name in ACADOS_OCP_QP_SOLVERS:
            runtime_fair = (
                qp_solver.get_stats("time_qp_xcond")
                + qp_solver.get_stats("time_qp_solver_call")
            )
        else:
            runtime_fair = runtime_external
        solver_sol = qp_solver.get_iterate()
        # TODO: reset() needed
        qp_solver = None

    ctx["status"] = status
    ctx["iterations"] = iter
    ctx["runtime_external"] = runtime_external
    ctx["runtime_internal"] = runtime_internal
    ctx["runtime_fair"] = runtime_fair
    # TODO: get_cost() needs to be called after solve()
    ctx["cost"] = 0.0

    return ctx, solver_sol


def compare_with_reference(
    json_path_dict: dict,
    solver_sol: AcadosOcpIterate,
    atol: float = 5e-5,
    rtol: float = 5e-5,
) -> None:
    """Compare a solver solution against the stored reference solution and log the result.

    Args:
        json_path_dict: Paths for the problem (qp_data_path, ref_sol_path, meta_data_path).
        solver_sol: The solution returned by the solver.
        atol: Absolute tolerance for the comparison.
        rtol: Relative tolerance for the comparison.
    """
    ref_path = json_path_dict["ref_sol_path"]
    data_path = json_path_dict["qp_data_path"]
    meta_path = json_path_dict["meta_data_path"]

    if not os.path.exists(ref_path):
        logging.error(f"\033[93m[MISSING REF]\033[0m Reference solution not found at: {ref_path}")
        return

    # Load and decompress reference solution
    json_data = decompress(ref_path)
    ref_sol = AcadosOcpIterate.from_json(json_data=json_data)

    # Verify solver solution against reference
    if ref_sol.allclose(solver_sol, atol=atol, rtol=rtol):
        logging.info(f"\033[92m[MATCH]\033[0m Solution matches reference for problem: {data_path}")
        return

    with open(meta_path, "r") as f:
        meta_dict = json.load(f)
    if meta_dict.get("definiteness", "") == "positive definite":
        logging.warning(f"\033[91m[MISMATCH]\033[0m Solution mismatch for problem: {data_path}")
    else:
        logging.warning(f"\033[93m[MISMATCH]\033[0m Solution mismatch for indefinite/semidefinite problem: {data_path} (may be expected)")


def run(
    test_set: TestSet,
    solver_set: SolverSet,
    results: Results,
    compare_sol: bool = True,
    print_level: int = 1,
) -> None:
    """Run a given test set and store results.

    Args:
        test_set: The test set containing problems to benchmark.
        solver_set: The set of solvers to benchmark.
        results: Results object to store benchmark results.
        print_level: Verbosity level.
    """
    if print_level == 0:
        logging.getLogger().setLevel(logging.ERROR)
    elif print_level == 1:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(logging.INFO)

    progress_bar = None
    if print_level > 0:
        nb_problems = test_set.count_problems()
        nb_solvers = len(solver_set)
        progress_bar = tqdm(
            total=nb_problems * nb_solvers,
            initial=0,
        )
    with logging_redirect_tqdm():
        for i, opts in enumerate(solver_set):
            solver_id = solver_set.solver_ids[i]
            if progress_bar is not None:
                progress_bar.set_description(f"Solver: {solver_id}")

            for json_path_dict in test_set:
                json_data = decompress(json_path_dict["qp_data_path"])
                qp = AcadosOcpQp.from_json(json_data=json_data)
                logging.info(
                    f"Solving problem {json_path_dict['qp_data_path']} "
                    f"with solver {solver_id}"
                )
                ctx, solver_sol = solve_problem(qp, opts)

                if compare_sol and solver_sol is not None:
                    compare_with_reference(json_path_dict, solver_sol)

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
