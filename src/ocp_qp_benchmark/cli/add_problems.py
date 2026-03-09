"""CLI for adding problems to the benchmark set."""

import argparse
from pathlib import Path

from ocp_qp_benchmark.dataset import BenchSetManager


def main():
    """
    Main entry point for adding problems.

    typically, the user will run this script as follows:
    add-problems /path/to/json/folder --name my_problems

    User should provide a folder containing JSON files containing the metrics of QP problems.
    For each QP JSON provided, add_problem will create:
    - {problem_name}.json: Copy form the provided QP problem data.
    - {problem_name}_meta.json: Some property of QP problem.
    - {problem_name}_ref_sol.json: the reference solution of QP problems solved by HPIPM. If the solver fails to find a solution, this file will be omitted.

    Args:
        folder_path: Path to folder containing JSON files of QPs for the problems.
        name: Name of the added problem set (default: qps).
    """
    parser = argparse.ArgumentParser(
        description="Add problems to benchmark set"
    )
    parser.add_argument(
        "folder_path", help="Path to folder containing JSON files"
    )
    parser.add_argument(
        "--name",
        "-n",
        default="qps",
        help="Name of the problem set to be added (default: qps)",
    )

    args = parser.parse_args()

    manager = BenchSetManager()
    manager.add_problems_from_json_folder(Path(args.folder_path), args.name)


if __name__ == "__main__":
    main()
