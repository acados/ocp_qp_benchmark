"""Main entry point for the OCP QP benchmark."""

import os

from acados_template import AcadosOcpQpOptions

from ocp_qp_benchmark.core import Results, TestSet, SolverSet, run
from ocp_qp_benchmark.core.solver_set import create_solver_options, get_solver_id
from ocp_qp_benchmark.visualization import plot_metric
from ocp_qp_benchmark.visualization.plotting import generate_labels

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


def main_run(solvers: list[AcadosOcpQpOptions], test_set: TestSet) -> None:
    """Run the benchmark.

    Args:
        solvers: List of solver configurations to benchmark.
        test_set: Test set containing problems.
    """
    solver_set = SolverSet(solvers=solvers)
    results = Results(file_path=RESULT_PATH, test_set=test_set)

    run(
        test_set,
        solver_set,
        results,
        print_level=2,
    )


def main():
    """Main entry point."""
    # Create solver configurations
    solvers = [
        create_solver_options("PARTIAL_CONDENSING_OSQP"),
        create_solver_options("PARTIAL_CONDENSING_HPIPM"),
        create_solver_options("PARTIAL_CONDENSING_CLARABEL"),
        create_solver_options("FULL_CONDENSING_QPOASES"),
        create_solver_options("FULL_CONDENSING_HPIPM"),
        create_solver_options("FULL_CONDENSING_DAQP"),
    ]

    # test_set
    all_problems = get_all_problems()
    test_set = TestSet(qp_folder_paths=all_problems)

    # main_run(solvers, test_set)

    # Generate labels based on differing options
    labels = generate_labels(solvers)

    # filtered
    filtered_test_set = test_set.filter_has_masks(False).filter_has_idxs_rev_not_idxs(
        False
    )
    filtered_test_set.description = "Problems without masks and idxs_rev"

    results = Results(file_path=RESULT_PATH, test_set=filtered_test_set)
    solver_ids = [get_solver_id(s) for s in solvers]
    plot_metric(
        metric="runtime_fair",
        df=results.df,
        test_set=filtered_test_set,
        solver_ids=solver_ids,
        labels=labels,
        linewidth=2.0,
        savefig="figures/qpbenchmark_runtime_filtered.pdf",
    )

    # full evaluation with subset of solvers
    eval_solvers = [
        create_solver_options("PARTIAL_CONDENSING_HPIPM"),
        create_solver_options("FULL_CONDENSING_HPIPM"),
        create_solver_options("FULL_CONDENSING_DAQP"),
    ]
    eval_labels = generate_labels(eval_solvers)
    eval_solver_ids = [get_solver_id(s) for s in eval_solvers]

    results = Results(file_path=RESULT_PATH, test_set=test_set)
    plot_metric(
        metric="runtime_fair",
        df=results.df,
        test_set=test_set,
        solver_ids=eval_solver_ids,
        labels=eval_labels,
        linewidth=2.0,
        savefig="figures/qpbenchmark_runtime.pdf",
    )


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
