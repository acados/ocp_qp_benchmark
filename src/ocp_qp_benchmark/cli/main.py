"""Main entry point for the OCP QP benchmark."""

import os

from ocp_qp_benchmark.core import Results, TestSet, SolverSet, run
from ocp_qp_benchmark.visualization import plot_metric

RESULT_PATH = "results/qpbenchmark_results.csv"


def get_all_problems(verbose: bool = True) -> list[str]:
    """Get all problems from the dataset collection.

    Args:
        verbose: Whether to print information about found folders.

    Returns:
        List of paths to problem folders.
    """
    ocp_dataset_path = "ocp_qp_dataset_collection"
    if not os.path.exists(ocp_dataset_path):
        raise FileNotFoundError(f"Directory {ocp_dataset_path} not found")

    subfolders = [
        f
        for f in os.listdir(ocp_dataset_path)
        if os.path.isdir(os.path.join(ocp_dataset_path, f))
    ]

    if verbose:
        print("Subfolders in ocp_qp_dataset_collection:")
        for folder in subfolders:
            print(f"  - {folder}")

    designated_problems = []
    for folder in subfolders:
        for qp_folder_name in os.listdir(os.path.join(ocp_dataset_path, folder)):
            designated_problems.append(
                os.path.join(ocp_dataset_path, folder, qp_folder_name)
            )
    return designated_problems


def main_run(
    solvers: list[str], test_set: TestSet, solver_settings: list[str]
) -> None:
    """Run the benchmark.

    Args:
        solvers: List of solver names to benchmark.
        test_set: Test set containing problems.
        solver_settings: List of solver settings to use.
    """
    solver_set = SolverSet(
        solvers=solvers,
        solver_settings=solver_settings,
    )
    results = Results(file_path=RESULT_PATH, test_set=test_set)

    run(
        test_set,
        solver_set,
        results,
        print_level=2,
    )


def main():
    """Main entry point."""
    solvers = [
        'PARTIAL_CONDENSING_OSQP',
        'PARTIAL_CONDENSING_HPIPM',
        'PARTIAL_CONDENSING_CLARABEL',
        'FULL_CONDENSING_QPOASES',
        "FULL_CONDENSING_HPIPM",
        'FULL_CONDENSING_DAQP',
    ]

    # test_set
    all_problems = get_all_problems()
    test_set = TestSet(
        qp_folder_paths=all_problems,
    )

    solver_settings = ["default"]
    main_run(solvers, test_set, solver_settings)

    # filtered
    filtered_test_set = test_set.filter_has_masks(False).filter_has_idxs_rev_not_idxs(
        False
    )
    filtered_test_set.description = "Problems without masks and idxs_rev"

    results = Results(file_path=RESULT_PATH, test_set=filtered_test_set)
    plot_metric(
        metric="runtime_fair",
        df=results.df,
        settings="default",
        test_set=filtered_test_set,
        solvers=solvers,
        linewidth=2.0,
        savefig="figures/qpbenchmark_runtime_filtered.pdf",
    )

    # full evaluation
    solvers = [
        "PARTIAL_CONDENSING_HPIPM",
        "FULL_CONDENSING_HPIPM",
        "FULL_CONDENSING_DAQP",
    ]
    results = Results(file_path=RESULT_PATH, test_set=test_set)
    plot_metric(
        metric="runtime_fair",
        df=results.df,
        settings="default",
        test_set=test_set,
        solvers=solvers,
        linewidth=2.0,
        savefig="figures/qpbenchmark_runtime.pdf",
    )


if __name__ == "__main__":
    main()
