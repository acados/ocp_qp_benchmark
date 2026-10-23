"""Display-label helpers for benchmark evaluation."""

import pandas


def solver_display_labels(df: pandas.DataFrame) -> pandas.Series:
    """Return configured solver labels, falling back to solver IDs."""
    if "solver_label" not in df.columns:
        return df["solver"]

    labels = df["solver_label"].fillna("").astype(str).str.strip()
    return labels.where(labels.ne(""), df["solver"])