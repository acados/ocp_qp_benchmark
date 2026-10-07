"""Plots for analysis of test set results."""

from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import pandas

from acados_template import latexify_plot

from ocp_qp_benchmark.core.test_set import TestSet

# Font sizes in pt
TITLE_FONTSIZE = 18
LABEL_FONTSIZE = 16
TICK_FONTSIZE = 14
LEGEND_FONTSIZE = 14

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
    linewidth: float = 2.5,
    savefig: Optional[str] = None,
    title: Optional[str] = None,
    latexify: bool = True,
    legend_loc: str = "lower right",
) -> None:
    """Plot comparing solvers on a given metric.

    Args:
        metric: Metric to compare solvers on.
        df: Test set results data frame.
        test_set: Test set.
        solver_ids: Solver IDs to compare (default: all in df).
        linewidth: Width of output lines, in px.
        savefig: If set, save plot to this path rather than displaying it.
        title: Plot title, set to "" to disable.
        latexify: Whether to apply LaTeX styling to the plot.
        legend_loc: Location of the legend.
    """
    if latexify:
        latexify_plot()

    assert pandas.api.types.is_numeric_dtype(df[metric])
    print(f"Plotting {metric} on {test_set.description}...")

    # Integer metrics (e.g. iterations) are drawn on a linear axis from zero,
    # float metrics (e.g. runtimes) on a log axis since they span orders of magnitude
    is_count_metric = pandas.api.types.is_integer_dtype(df[metric])

    total_problems = test_set.count_problems()
    solved_df = df[df["status"] == 0]

    plot_solver_ids: List[str] = (
        solver_ids if solver_ids is not None else list(set(solved_df.solver))
    )

    # Assign one color per solver from the tab10 palette
    palette = plt.get_cmap("tab10").colors
    solver_colors = {
        solver_id: palette[i % len(palette)]
        for i, solver_id in enumerate(plot_solver_ids)
    }

    # Short labels, with a counter to distinguish solvers sharing a name
    labels = {}
    seen = {}
    for solver_id in plot_solver_ids:
        name = _shorten_solver_name(solver_id)
        seen[name] = seen.get(name, 0) + 1
        labels[solver_id] = f"{name}_{seen[name] - 1}"

    # Collect sorted metric values of solved problems for each solver
    solver_values = {}
    for solver_id in plot_solver_ids:
        values = solved_df[solved_df["solver"] == solver_id][metric].values
        if len(values) == 0:
            print(f"Warning: no values to plot for solver {solver_id}")
            continue
        solver_values[solver_id] = np.sort(values)

    # Shared x-range so that all curves start and end at the same place
    if solver_values:
        min_value = min(values[0] for values in solver_values.values())
        max_value = max(values[-1] for values in solver_values.values())
    else:
        min_value, max_value = 1.0, 1.0
    min_x_limit = 0 if is_count_metric else min_value * 0.95
    max_x_limit = max_value * 1.05

    fig, ax = plt.subplots(figsize=(9, 7))

    # Plot step functions
    for solver_id, solved_values in solver_values.items():
        nb_solved = len(solved_values)

        # Start at zero solved problems and extend the last level to the right edge
        x_plot = np.concatenate(([min_x_limit], solved_values, [max_x_limit]))
        y_plot = np.concatenate(([0], np.arange(1, nb_solved + 1), [nb_solved]))

        ax.step(x_plot, y_plot, where="post", label=labels[solver_id],
                color=solver_colors[solver_id], linewidth=linewidth, alpha=0.85)
        ax.plot(solved_values[-1], nb_solved, marker="o",
                color=solver_colors[solver_id], markersize=8)

    # Format plot
    ax.axhline(total_problems, color="black", linestyle="--", linewidth=1.5, alpha=0.5)
    ax.text(min_x_limit, total_problems, f" Total Problems: {total_problems}",
            va="bottom", ha="left", color="gray", fontsize=TICK_FONTSIZE)

    if title is None:
        title = f"{test_set.title}"
    if title != "":
        ax.set_title(title, fontsize=TITLE_FONTSIZE, pad=12)
    ax.set_xlabel(metric, fontsize=LABEL_FONTSIZE, labelpad=8)
    ax.set_ylabel("Solved Problems (Count)", fontsize=LABEL_FONTSIZE, labelpad=8)
    ax.set_xlim(min_x_limit, max_x_limit)
    ax.set_ylim(0, total_problems * 1.2)
    if is_count_metric:
        ax.set_xscale("linear")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    else:
        ax.set_xscale("log")

    # Scale axes frame and ticks to match the font size
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
    ax.tick_params(which="major", labelsize=TICK_FONTSIZE, length=6, width=1.2)
    ax.tick_params(which="minor", labelsize=TICK_FONTSIZE, length=3.5, width=0.9)

    ax.grid(True, which="both", ls="--", linewidth=0.8, alpha=0.3)
    ax.legend(loc=legend_loc, frameon=True, fontsize=LEGEND_FONTSIZE)

    plt.tight_layout()

    if savefig:
        fig.savefig(savefig, bbox_inches="tight")
        print(f"Saved plot to {savefig}")
        plt.close(fig)
    else:
        plt.show(block=True)
