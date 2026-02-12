"""Plots for analysis of test set results."""

from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas

from ocp_qp_benchmark.core.test_set import TestSet
from acados_template import latexify_plot


def plot_metric(
    metric: str,
    df: pandas.DataFrame,
    settings: str,
    test_set: TestSet,
    solvers: Optional[List[str]] = None,
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
        settings: Settings to compare solvers on.
        test_set: Test set.
        solvers: Names of solvers to compare (default: all).
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
    print(
        f"Plotting {metric} for {settings} settings on {test_set.description}..."
    )
    nb_problems = test_set.count_problems()
    settings_df = df[df["settings"] == settings]
    solved_df = settings_df[settings_df["status"] == 0]
    plot_solvers: List[str] = (
        solvers if solvers is not None else list(set(solved_df.solver))
    )

    n_solvers = len(plot_solvers)
    colors = [f"C{i}" for i in range(n_solvers)]
    linestyles = ["-", "--", "-.", ":"] * (n_solvers // 4 + 1)

    # First, collect all values for each solver
    solver_values = {}
    max_value = 0
    for solver in plot_solvers:
        values = solved_df[solved_df["solver"] == solver][metric].values
        if len(values) == 0:
            print(
                f"Warning: no values to plot for solver {solver} "
                f"with settings {settings}"
            )
            continue
        sorted_values = np.sort(values)
        solver_values[solver] = sorted_values
        max_value = max(
            max_value, sorted_values[-1] if len(sorted_values) > 0 else 0
        )

    # Second, plot all solvers with same max x value
    for i, (solver, values) in enumerate(solver_values.items()):
        nb_solved = len(values)
        y = np.arange(1, 1 + nb_solved)
        padded_values = np.hstack([values, [max_value]])
        padded_y = np.hstack([y, [nb_solved]])
        plt.step(
            padded_values,
            padded_y,
            linewidth=linewidth,
            label=solver,
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
