"""Markdown reports for benchmark results."""

import pandas


def status_counts_markdown(df: pandas.DataFrame) -> str:
    """Return Markdown counts with solvers as rows and statuses as columns."""
    required_columns = {"solver", "status"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Results are missing required columns: {missing}")

    counts = pandas.crosstab(df["solver"], df["status"])
    counts = counts.reindex(
        index=sorted(counts.index), columns=sorted(counts.columns), fill_value=0
    ).astype(int)

    headers = ["Solver", *(str(status) for status in counts.columns)]
    rows = [[str(solver).replace("|", r"\|") , *(str(value) for value in values)]
            for solver, values in counts.iterrows()]
    separator = ["---", *("---:" for _ in counts.columns)]
    table = [headers, separator, *rows]
    return "\n".join("| " + " | ".join(row) + " |" for row in table)