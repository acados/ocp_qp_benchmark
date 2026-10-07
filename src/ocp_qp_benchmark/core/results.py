"""Benchmark results."""

import json
from pathlib import Path
from typing import Union

import pandas

# Result columns and their dtypes
COLUMNS = {
    "problem": str,
    "solver": str,
    "cost": float,
    "iterations": int,
    "runtime_external": float,
    "runtime_internal": float,
    "runtime_fair": float,
    "status": int,
}


class Results:
    """
    Collect benchmark results and save them to a CSV or Parquet file.

    Any existing file at `file_path` is deleted on creation, so every run
    starts from a clean results file.

    Example:
        results = Results("results/qpbenchmark_results.csv")
        results.update(meta_data_path, solver_id, ctx)
        results.write()
        results.df  # one row per (problem, solver) pair

    Attributes:
        file_path: Path to the results file.
    """

    def __init__(self, file_path: Union[str, Path]):
        """Initialize results and delete any existing file at `file_path`.

        Args:
            file_path: Path to the results file, ending in `.csv` or `.parquet`.
        """
        self.file_path = Path(file_path)
        if self.file_path.suffix not in (".csv", ".parquet"):
            raise ValueError(
                f"Results file must end in .csv or .parquet, got: {file_path}"
            )
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.unlink(missing_ok=True)
        self._rows: dict[tuple[str, str], dict] = {}

    @property
    def df(self) -> pandas.DataFrame:
        """Results data frame, sorted by problem and solver."""
        df = pandas.DataFrame(self._rows.values(), columns=list(COLUMNS))
        return df.astype(COLUMNS).sort_values(
            by=["problem", "solver"], ignore_index=True
        )

    def update(self, problem: Path, solver_id: str, context: dict) -> None:
        """Add or overwrite the entry for a given (problem, solver) pair.

        Args:
            problem: Path to problem meta file.
            solver_id: Solver identifier string.
            context: Solution context containing status, iterations, etc.
        """
        with open(problem, "r") as f:
            problem_name = json.load(f)["name"].split(".")[0]

        row = {"problem": problem_name, "solver": solver_id}
        row.update({col: context[col] for col in COLUMNS if col not in row})
        self._rows[(problem_name, solver_id)] = row

    def write(self) -> None:
        """Write results to `file_path`."""
        if self.file_path.suffix == ".parquet":
            self.df.to_parquet(self.file_path, index=False)
        else:
            self.df.to_csv(self.file_path, index=False)

    def get_solver_ids(self) -> list[str]:
        """Get list of unique solver IDs in results."""
        return list(self.df["solver"].unique())