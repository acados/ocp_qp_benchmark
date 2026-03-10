"""Main entry point for the OCP QP benchmark."""

import os

from acados_template import AcadosOcpQpOptions

from ocp_qp_benchmark.core import TestSet, SolverSet, Result, run
from ocp_qp_benchmark.visualization import plot_metric

RESULT_PATH = "results/qpbenchmark_results.csv"

def get_all_problems(verbose: bool = True) -> list[str]:
    """Get all problems from the dataset collection.

    Args:
        verbose: Whether to print information about found folders.

    Returns:
        List of paths to problem folders.
        e.g., ["ocp_qp_dataset_collection/random_qp/prob_0", ...]
    """
    ocp_dataset_path = "ocp_qp_dataset_collection"
    if not os.path.exists(ocp_dataset_path):
        raise FileNotFoundError(f"Directory {ocp_dataset_path} not found")

    subfolders = [
        f
        for f in os.listdir(ocp_dataset_path)
        if os.path.isdir(os.path.join(ocp_dataset_path, f))
    ]
    # filter
    subfolders = [f for f in subfolders if f.startswith("random_qp")]

    designated_problems = []
    for folder in subfolders:
        for qp_folder_name in os.listdir(os.path.join(ocp_dataset_path, folder)):
            designated_problems.append(
                os.path.join(ocp_dataset_path, folder, qp_folder_name)
            )
    return designated_problems

def main():
    """
    OCP QP Benchmark main file
    Also a example for setting up benchmark
    """

    ## Create test_set ##
    # get problems and create test set
    example_qp_folders = get_all_problems()
    test_set = TestSet(qp_folder_paths=example_qp_folders)
    # filter problems
    test_set.filter_problems(
        {
            "has_masks": False, 
            "has_idxs_rev_not_idxs": False
        }
    )
    # define description for test set
    test_set.description = "Problems without masks and idxs_rev"

    ## Create solver set ##
    # sepcify sovlers and corresponding options to be evaluated
    designated_solver_dict = (
        {'PARTIAL_CONDENSING_OSQP': {}},
        {'PARTIAL_CONDENSING_HPIPM': {}},
        {'PARTIAL_CONDENSING_HPIPM': {'iter_max': 500}},
        {'PARTIAL_CONDENSING_CLARABEL': {}},
        {'FULL_CONDENSING_QPOASES': {}},
        {'FULL_CONDENSING_HPIPM': {}},
        {'FULL_CONDENSING_DAQP': {}},
    ) # {} indicates default options for each solver
    # Generate labels based on differing options
    solver_set = SolverSet(solver_dicts = designated_solver_dict)

    ## Create Results logger ##
    results = Result(file_path=RESULT_PATH, test_set=test_set)

    ## Run benchmark ##
    run(
        test_set,
        solver_set,
        results,
        print_level=2,
    )

    ## Plotting ##
    plot_metric(
        metric="runtime_fair",
        df=results.df,
        solver_ids=solver_set.solver_ids,
        test_set=test_set,
        linewidth=2.0,
        savefig="figures/qpbenchmark_runtime_filtered.pdf",
    )

    ## Evaluate ##
    # specify solvers to be evaluated
    eval_solver_names = [
        'PARTIAL_CONDENSING_HPIPM',
        'FULL_CONDENSING_HPIPM'
    ]
    # filter solver_ids based on specified eval_solver_name
    eval_solver_ids = solver_set.get_solver_ids_by_names(eval_solver_names)

    results = Result(file_path=RESULT_PATH, test_set=test_set)
    plot_metric(
        metric="runtime_fair",
        df=results.df,
        solver_ids=eval_solver_ids,
        test_set=test_set,
        linewidth=2.0,
        savefig="figures/qpbenchmark_runtime.pdf",
    )

if __name__ == "__main__":
    main()