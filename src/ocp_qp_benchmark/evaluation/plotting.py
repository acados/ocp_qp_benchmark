"""Plots for analysis of test set results."""

from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import pandas

from acados_template import latexify_plot
from .labels import solver_display_labels

# Font sizes in pt
TITLE_FONTSIZE = 18
LABEL_FONTSIZE = 16
TICK_FONTSIZE = 14
LEGEND_FONTSIZE = 14


def _shorten_solver_name(name: str) -> str:
    """Shorten solver name for plot labels."""
    split_text = name.split("_")
    solver_name = "_".join([part for part in split_text if part.isupper()])
    short_name = solver_name.replace("PARTIAL_CONDENSING", "PCOND")
    short_name = short_name.replace("FULL_CONDENSING", "FCOND")
    return short_name


def _successful_rows(df: pandas.DataFrame) -> pandas.DataFrame:
    """Include failures only for problems with no reference and no solver success."""
    successful = df[df["status"] == 0]
    if "has_reference_solution" not in df.columns:
        return successful

    has_reference = df.groupby("problem")["has_reference_solution"].any()
    all_solvers_failed = (df["status"] != 0).groupby(df["problem"]).all()
    infeasible_problems = has_reference.index[
        ~has_reference & all_solvers_failed.reindex(has_reference.index, fill_value=False)
    ]
    failed_infeasible = df[df["problem"].isin(infeasible_problems)]
    return pandas.concat([successful, failed_infeasible])


def plot_metric(
    metric: str,
    df: pandas.DataFrame,
    solver_ids: Optional[List[str]] = None,
    linewidth: float = 2.5,
    savefig: Optional[str] = None,
    title: Optional[str] = None,
    latexify: bool = True,
    legend_loc: str = "lower right",
) -> None:
    """Plot comparing solvers on a given metric."""
    if latexify:
        latexify_plot()

    assert pandas.api.types.is_numeric_dtype(df[metric])
    total_problems = df["problem"].nunique()
    plot_title = title or ""
    print(f"Plotting {metric}...")
    is_count_metric = pandas.api.types.is_integer_dtype(df[metric])
    solved_df = _successful_rows(df)
    plot_solver_ids: List[str] = (
        solver_ids if solver_ids is not None else list(set(solved_df.solver))
    )
    display_labels = pandas.DataFrame(
        {"solver": df["solver"], "label": solver_display_labels(df)}
    ).drop_duplicates("solver").set_index("solver")["label"]

    palette = plt.get_cmap("tab10").colors
    solver_colors = {
        solver_id: palette[i % len(palette)]
        for i, solver_id in enumerate(plot_solver_ids)
    }

    labels = {}
    seen = {}
    for solver_id in plot_solver_ids:
        configured_label = display_labels.get(solver_id, "")
        name = (
            configured_label
            if configured_label != solver_id
            else _shorten_solver_name(solver_id)
        )
        seen[name] = seen.get(name, 0) + 1
        labels[solver_id] = (
            f"{name}_{seen[name] - 1}"
            if configured_label == solver_id
            else name if seen[name] == 1 else f"{name}_{seen[name] - 1}"
        )

    solver_values = {}
    for solver_id in plot_solver_ids:
        values = solved_df[solved_df["solver"] == solver_id][metric].values
        if len(values) == 0:
            print(f"Warning: no values to plot for solver {solver_id}")
            continue
        solver_values[solver_id] = np.sort(values)

    if solver_values:
        min_value = min(values[0] for values in solver_values.values())
        max_value = max(values[-1] for values in solver_values.values())
    else:
        min_value, max_value = 1.0, 1.0
    min_x_limit = 0 if is_count_metric else min_value * 0.95
    max_x_limit = max_value * 1.05

    fig, ax = plt.subplots(figsize=(9, 7))
    for solver_id, solved_values in solver_values.items():
        nb_solved = len(solved_values)
        x_plot = np.concatenate(([min_x_limit], solved_values, [max_x_limit]))
        y_plot = np.concatenate(([0], np.arange(1, nb_solved + 1), [nb_solved]))
        ax.step(x_plot, y_plot, where="post", label=labels[solver_id],
                color=solver_colors[solver_id], linewidth=linewidth, alpha=0.85)
        ax.plot(solved_values[-1], nb_solved, marker="o",
                color=solver_colors[solver_id], markersize=8)

    ax.axhline(total_problems, color="black", linestyle="--", linewidth=1.5, alpha=0.5)
    ax.text(min_x_limit, total_problems, f" Total Problems: {total_problems}",
            va="bottom", ha="left", color="gray", fontsize=TICK_FONTSIZE)
    if plot_title != "":
        ax.set_title(plot_title, fontsize=TITLE_FONTSIZE, pad=12)
    ax.set_xlabel(metric, fontsize=LABEL_FONTSIZE, labelpad=8)
    ax.set_ylabel("Solved Problems (Count)", fontsize=LABEL_FONTSIZE, labelpad=8)
    ax.set_xlim(min_x_limit, max_x_limit)
    ax.set_ylim(0, total_problems * 1.2)
    if is_count_metric:
        ax.set_xscale("linear")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    else:
        ax.set_xscale("log")

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