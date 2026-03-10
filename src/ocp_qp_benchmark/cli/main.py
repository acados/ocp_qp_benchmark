"""Main entry point for the OCP QP benchmark."""

import argparse
import os

from acados_template import AcadosOcpQpOptions

from ocp_qp_benchmark.core import TestSet, SolverSet, Result, run
from ocp_qp_benchmark.core.supported_solvers import (
    ACADOS_OCP_QP_SOLVERS,
    ACADOS_CASADI_SOLVERS,
    EXTERNAL_SOLVERS,
)
from ocp_qp_benchmark.visualization import plot_metric

RESULT_PATH = "results/qpbenchmark_results.csv"

def get_all_problems() -> list[str]:
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

    Users can run this script with default solver setting as follows:
    ocp-benchmark -f ocp_qp_dataset_collection/random_qp -s PARTIAL_CONDENSING_OSQP,PARTIAL_CONDENSING_HPIPM
    """

    parser = argparse.ArgumentParser(
        description="run OCP QP benchmark"
    )
    parser.add_argument(
        "--folder_path",
        "-f", 
        default=None,
        help="Path to folder containing JSON folders of QPs for the problems. (defualt: None, which will use all problems in ocp_qp_dataset_collection)",
    )
    parser.add_argument(
        "--solvers",
        "-s",
        default=None,
        help="Name of the OCP QP solvers with default setting (default: None, which will use all AcadosOcpQpsolver with default setting)",
    )

    args = parser.parse_args()

    ## Create test_set ##
    # get problems and create test set
    example_qp_folders = get_all_problems() if args.folder_path is None else [os.path.join(args.folder_path, f) for f in os.listdir(args.folder_path)]
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
    if args.solvers is None:
        designated_solver_list = [
            ('PARTIAL_CONDENSING_OSQP', {}),
            ('PARTIAL_CONDENSING_HPIPM', {}),
            ('PARTIAL_CONDENSING_HPIPM', {'iter_max': 500}),
            ('PARTIAL_CONDENSING_CLARABEL', {}),
            ('FULL_CONDENSING_QPOASES', {}),
            ('FULL_CONDENSING_HPIPM', {}),
            ('FULL_CONDENSING_DAQP', {}),
        ] # {} indicates default options for each solver
    else:
        designated_solver_list = []
        for solver_name in args.solvers.split(","):
            solver_name = solver_name.strip()
            if solver_name in ACADOS_OCP_QP_SOLVERS:
                designated_solver_list.append((solver_name, {}))
            elif solver_name in ACADOS_CASADI_SOLVERS or solver_name in EXTERNAL_SOLVERS:
                raise NotImplementedError(f"Casadi and external solvers not implemented yet, cannot add {solver_name}")
            else:
                raise ValueError(f"Unknown solver name: {solver_name}")
    # Generate labels based on differing options
    solver_set = SolverSet(solver_list = designated_solver_list)

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
    if args.solvers is None:
        eval_solver_names = [
            'PARTIAL_CONDENSING_HPIPM',
            'FULL_CONDENSING_HPIPM'
        ] # evaluate solvers by default
    else:
        eval_solver_names = args.solvers.split(",")

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