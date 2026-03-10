"""Plots for analysis of test set results."""

from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas

from acados_template import latexify_plot

from ocp_qp_benchmark.core.test_set import TestSet

def _shorten_solver_name(name: str) -> str:
    """Shorten solver name for plot labels."""
    # Remove common prefixes
    split_text = name.split("_")
    solver_name = "_".join([part for part in split_text if part.isupper()])
    short_name = solver_name.replace("PARTIAL_CONDENSING", "PCOND")
    short_name = short_name.replace("FULL_CONDENSING", "FCOND")
    return short_name

def plot_metric(
    metric: str,
    df: pandas.DataFrame,
    test_set: TestSet,
    solver_ids: Optional[List[str]] = None,
    linewidth: float = 2.0,
    savefig: Optional[str] = None,
    title: Optional[str] = None,
    latexify: bool = True,
    legend_loc: str = "best",
) -> None:
    """Plot comparing solvers on a given metric.

    Args:
        metric: Metric to compare solvers on.
        df: Test set results data frame.
        test_set: Test set.
        solver_ids: Solver IDs to compare (default: all in df).
        labels: Custom labels for solvers (maps solver_id to label).
        linewidth: Width of output lines, in px.
        savefig: If set, save plot to this path rather than displaying it.
        title: Plot title, set to "" to disable.
        latexify: Whether to apply LaTeX styling to the plot.
        legend_loc: Location of the legend.
    """
    if latexify:
        latexify_plot()

    plt.figure()

    assert issubclass(df[metric].dtype.type, np.floating)
    print(f"Plotting {metric} on {test_set.description}...")

    nb_problems = test_set.count_problems()
    solved_df = df[df["status"] == 0]

    plot_solver_ids: List[str] = (
        solver_ids if solver_ids is not None else list(set(solved_df.solver))
    )

    n_solvers = len(plot_solver_ids)
    colors = [f"C{i}" for i in range(n_solvers)]
    linestyles = ["-", "--", "-.", ":"] * (n_solvers // 4 + 1)

    # Default labels: use solver_id directly
    labels = {}
    seen = {}
    for sid in plot_solver_ids:
        name = _shorten_solver_name(sid)
        seen[name] = seen.get(name, 0) + 1
        labels[sid] = f"{name}_{seen[name] - 1}"

    # First, collect all values for each solver
    solver_values = {}
    max_value = 0
    for solver_id in plot_solver_ids:
        values = solved_df[solved_df["solver"] == solver_id][metric].values
        if len(values) == 0:
            print(f"Warning: no values to plot for solver {solver_id}")
            continue
        sorted_values = np.sort(values)
        solver_values[solver_id] = sorted_values
        max_value = max(
            max_value, sorted_values[-1] if len(sorted_values) > 0 else 0
        )

    # Second, plot all solvers with same max x value
    for i, (solver_id, values) in enumerate(solver_values.items()):
        nb_solved = len(values)
        y = np.arange(1, 1 + nb_solved)
        padded_values = np.hstack([values, [max_value]])
        padded_y = np.hstack([y, [nb_solved]])
        label = labels.get(solver_id, solver_id)
        plt.step(
            padded_values,
            padded_y,
            linewidth=linewidth,
            label=label,
            color=colors[i],
            linestyle=linestyles[i],
        )

    plt.legend(loc=legend_loc)
    if title is None:
        title = f"{test_set.title}"
    if title != "":
        plt.title(title)
    plt.xlabel(metric)
    plt.xscale("log")
    plt.axhline(y=nb_problems, color="gray", linestyle=":", linewidth=linewidth)
    plt.ylim(0, nb_problems * 1.05)
    plt.ylabel("problems solved")
    plt.grid(True)
    if savefig:
        plt.savefig(fname=savefig)
        print(f"Saved plot to {savefig}")
    else:
        plt.show(block=True)
