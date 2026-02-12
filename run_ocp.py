import numpy as np
from time import perf_counter

from tqdm import tqdm
from test_set_ocp import TestSet
from solver_set_ocp import SolverSet
from results_ocp import Results

from acados_template import AcadosOcpSolver, AcadosOcpQp, AcadosOcpQpSolver, AcadosOcpQpOptions

def solve_problem(qp: AcadosOcpQp, solver: str, solver_settings, repeat_times: int = 1, print_level: int = 0) -> dict:
    ctx = {}
    runtime_external = 1e50

    if repeat_times != 1:
        raise NotImplementedError("repeat_times != 1 not implemented yet")

    for _ in range(repeat_times):
        opts = AcadosOcpQpOptions()
        opts.qp_solver = solver
        opts.print_level = print_level-1
        opts.iter_max = 1000
        try:
            qp_solver = AcadosOcpQpSolver(qp, opts)
        except Exception as e:
            if print_level > 0:
                print(f"Error initializing solver {solver} got error:\n {e}")
            ctx['status'] = -1 # ACADOS_UNKNOWN
            ctx['iterations'] = -1
            ctx['runtime_external'] = -1
            ctx['runtime_internal'] = -1
            ctx['runtime_fair'] = -1
            ctx['cost'] = np.nan
            return ctx
        start_time = perf_counter()
        status = qp_solver.solve()
        if print_level > 0 and status != 0:
            print(f"Solver {solver} failed with status {status}")
        runtime_external = min(runtime_external, perf_counter() - start_time)
        iter = qp_solver.get_stats('iter')
        runtime_internal = qp_solver.get_stats('time_tot')
        runtime_fair = qp_solver.get_stats('time_qp_xcond') + qp_solver.get_stats('time_qp_solver_call')
        # TODO: reset() needed
        qp_solver = None

    ctx['status'] = status
    ctx['iterations'] = iter
    ctx['runtime_external'] = runtime_external
    ctx['runtime_internal'] = runtime_internal
    ctx['runtime_fair'] = runtime_fair
    # TODO: get_cost() needs to be called after solve()
    ctx['cost'] = 0.0

    # if status != 0:
    #     breakpoint()
    return ctx

def run(
    test_set: TestSet,
    solver_set: SolverSet,
    results: Results,
    print_level: int = 1,
) -> None:
    """Run a given test set and store results.
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
            progress_bar.set_description(f"Solver: {solver}, Setting: {solver_settings}")
            for json_path_dict in test_set:
                qp = AcadosOcpQp.from_json(json_path_dict['qp_data_path'])
                if print_level > 1:
                    print(f"Solving problem {json_path_dict['qp_data_path']} with solver {solver} and settings {solver_settings}")
                ctx = solve_problem(qp, solver, solver_settings, print_level=print_level-1)
                results.update(json_path_dict['meta_data_path'], solver, solver_settings, ctx)
                if progress_bar is not None:
                    progress_bar.update(1)
        results.write()

    if progress_bar is not None:
        progress_bar.close()
