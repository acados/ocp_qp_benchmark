"""Main entry point for the OCP QP benchmark."""

import argparse
import os
import json

from acados_template import AcadosOcpQpOptions

from ocp_qp_benchmark.core import TestSet, SolverSet, Results, run
from ocp_qp_benchmark.core.supported_solvers import (
    ACADOS_OCP_QP_SOLVERS,
    ACADOS_CASADI_SOLVERS,
    EXTERNAL_SOLVERS,
)
from ocp_qp_benchmark.visualization import plot_metric

RESULT_PATH = "results/qpbenchmark_results.csv"

def parse_options(arg_list = None) -> dict:
    parser = argparse.ArgumentParser(
        description="run OCP QP benchmark"
    )
    parser.add_argument(
        "-c", "--configs_path",
        type=str,
        required=True,
        help="Path to JSON file for configs of benchmark run.",
    )

    args = parser.parse_args(arg_list)

    with open(args.configs_path, 'r') as f:
        config_dict = json.load(f)

    return config_dict

def get_problems(test_subset_path) -> list[str]:
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

    designated_problems = []
    for test_subset in test_subset_path:
        problems = [os.path.join(test_subset, f) for f in os.listdir(test_subset)]
        designated_problems.extend(problems)
    return designated_problems

def main(config_json: dict):
    """
    OCP QP Benchmark main file
    Also a example for setting up benchmark

    Users can run this script with default solver setting as follows:
    ocp-benchmark -c tests/benchmark.json
    """

    test_subset_path = config_json.get("test_setting", None)
    test_filter = config_json.get("test_filter_setting", None)
    test_description = config_json.get("test_description", "")
    solver_setting = config_json.get("solver_setting", None)

    ## Create test_set ##
    # get problems and create test set
    example_qp_folders = get_problems(test_subset_path)
    test_set = TestSet(qp_folder_paths=example_qp_folders)
    # filter problems
    test_set.filter_problems(test_filter)
    # define description for test set
    test_set.description = test_description

    ## Create solver set ##
    # sepcify sovlers and corresponding options to be evaluated
    designated_solver_list = solver_setting
    # Generate labels based on differing options
    solver_set = SolverSet(solver_list = designated_solver_list)

    ## Create Results logger ##
    results = Results(file_path=RESULT_PATH, test_set=test_set)

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
    eval_solver_names = config_json.get("eval_solver_names", None)
    # filter solver_ids based on specified eval_solver_name
    eval_solver_ids = solver_set.get_solver_ids_by_names(eval_solver_names)

    results = Results(file_path=RESULT_PATH, test_set=test_set)
    plot_metric(
        metric="runtime_fair",
        df=results.df,
        solver_ids=eval_solver_ids,
        test_set=test_set,
        linewidth=2.0,
        savefig="figures/qpbenchmark_runtime.pdf",
    )

if __name__ == "__main__":
    # test_cli_input = ["-c", "tests/benchmark.json"]
    # config_dict = parse_options(arg_list=test_cli_input)
    config_dict = parse_options()
    main(config_dict)