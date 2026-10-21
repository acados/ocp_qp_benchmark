"""Command-line entry point for benchmark runs and result plotting."""

import argparse
import json
from pathlib import Path
from typing import Optional

from ocp_qp_benchmark.core import Results, SolverSet, TestSet, run
from ocp_qp_benchmark.visualization import plot_metric

RESULT_PATH = Path("results/qpbenchmark_results.csv")
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_problems(test_subset_path: list[str]) -> list[str]:
    """Get all problems from the dataset collection.

    Args:
        verbose: Whether to print information about found folders.

    Returns:
        List of paths to problem folders.
        e.g., ["ocp_qp_dataset_collection/random_qp/prob_0", ...]
    """
    ocp_dataset_path = PROJECT_ROOT / "ocp_qp_dataset_collection"
    if not ocp_dataset_path.exists():
        raise FileNotFoundError(f"Dataset collection not found: {ocp_dataset_path}")

    designated_problems = []
    for test_subset in test_subset_path:
        subset_path = ocp_dataset_path / test_subset
        if not subset_path.is_dir():
            raise FileNotFoundError(f"Dataset not found: {subset_path}")
        problems = [str(path) for path in subset_path.iterdir()]
        designated_problems.extend(problems)
    return designated_problems


def run_from_config(config_path: str, results_path: str = str(RESULT_PATH)) -> None:
    """Run a benchmark described by a JSON configuration file."""
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    test_subset_path = config_json.get("test_setting", None)
    test_filter = config_json.get("test_filter_setting", None)
    test_description = config_json.get("test_description", "")
    solver_setting = config_json.get("solver_setting", None)
    compare_bool = config_json.get("compare_sol", False)
    example_qp_folders = get_problems(test_subset_path)
    test_set = TestSet(qp_folder_paths=example_qp_folders)
    # filter problems
    test_set.filter_problems(test_filter)
    # define description for test set
    test_set.description = test_description.strip().replace(" ", "_").lower()

    solver_set = SolverSet(solver_list=solver_setting)
    results = Results(results_path)
    run(
        test_set,
        solver_set,
        results,
        compare_sol=compare_bool,
        print_level=2,
    )

def plot_results(
    results_path: str,
    metric: str = "runtime_fair",
    solver_ids: Optional[list[str]] = None,
    output_path: Optional[str] = None,
    title: Optional[str] = None,
    latexify: bool = True,
) -> None:
    """Create a plot from a saved CSV or Parquet results file."""
    df = Results.load_dataframe(results_path)
    if metric not in df.columns:
        raise ValueError(
            f"Unknown metric '{metric}'. Available columns: {', '.join(df.columns)}"
        )

    available_solver_ids = list(df["solver"].drop_duplicates())
    if solver_ids is not None:
        unknown_ids = sorted(set(solver_ids) - set(available_solver_ids))
        if unknown_ids:
            raise ValueError(
                f"Unknown solver IDs: {', '.join(unknown_ids)}. "
                f"Available solver IDs: {', '.join(available_solver_ids)}"
            )

    if output_path is None:
        output_path = str(Path("figures") / f"{Path(results_path).stem}_{metric}.pdf")

    plot_metric(
        metric=metric,
        df=df,
        solver_ids=solver_ids,
        savefig=output_path,
        title=title,
        latexify=latexify,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark OCP QP solvers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a benchmark")
    run_parser.add_argument(
        "-c", "--config", required=True, help="JSON benchmark configuration"
    )
    run_parser.add_argument(
        "--results",
        default=str(RESULT_PATH),
        help=f"Output CSV or Parquet file (default: {RESULT_PATH})",
    )

    plot_parser = subparsers.add_parser("plot", help="Plot saved benchmark results")
    plot_parser.add_argument("--results", required=True, help="Input CSV or Parquet file")
    plot_parser.add_argument(
        "--metric", default="runtime_fair", help="Numeric result column to plot"
    )
    plot_parser.add_argument(
        "--solver-ids",
        nargs="+",
        default=None,
        help="Exact solver IDs to include (default: all solver IDs)",
    )
    plot_parser.add_argument("--output", help="Output plot path (default: figures/<results>_<metric>.pdf)")
    plot_parser.add_argument("--title", help="Optional plot title")
    plot_parser.add_argument(
        "--no-latexify",
        dest="latexify",
        action="store_false",
        help="Disable LaTeX plot styling",
    )
    plot_parser.set_defaults(latexify=True)
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        run_from_config(args.config, args.results)
    elif args.command == "plot":
        plot_results(
            args.results,
            args.metric,
            args.solver_ids,
            args.output,
            args.title,
            args.latexify,
        )


if __name__ == "__main__":
    main()