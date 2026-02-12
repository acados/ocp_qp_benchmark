"""Plots for analysis of test set results."""

from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas

from acados_template import AcadosOcpQpOptions, latexify_plot

from ocp_qp_benchmark.core.test_set import TestSet
from ocp_qp_benchmark.core.solver_set import get_solver_id


def generate_labels(
    solvers: List[AcadosOcpQpOptions],
) -> Dict[str, str]:
    """Generate plot labels showing only the options that differ between solvers.

    Args:
        solvers: List of solver option configurations.

    Returns:
        Dictionary mapping solver_id to display label.
    """
    if len(solvers) == 0:
        return {}

    if len(solvers) == 1:
        return {get_solver_id(solvers[0]): solvers[0].qp_solver}

    # Collect all attribute values
    attrs_to_check = [
        "qp_solver",
        "tol_stat",
        "tol_eq",
        "tol_ineq",
        "tol_comp",
        "iter_max",
        "cond_N",
    ]

    # Find which attributes differ
    differing_attrs = []
    for attr in attrs_to_check:
        values = [getattr(opts, attr) for opts in solvers]
        if len(set(str(v) for v in values)) > 1:
            differing_attrs.append(attr)

    # Generate labels based on differing attributes
    labels = {}
    for opts in solvers:
        solver_id = get_solver_id(opts)

        if not differing_attrs:
            # All same, just use qp_solver name
            labels[solver_id] = opts.qp_solver
        elif differing_attrs == ["qp_solver"]:
            # Only solver differs, use short name
            labels[solver_id] = _shorten_solver_name(opts.qp_solver)
        else:
            # Multiple things differ, show them
            parts = []
            for attr in differing_attrs:
                value = getattr(opts, attr)
                if attr == "qp_solver":
                    parts.append(_shorten_solver_name(value))
                elif isinstance(value, float) and value < 0.01:
                    parts.append(f"{attr}={value:.0e}")
                else:
                    parts.append(f"{attr}={value}")
            labels[solver_id] = ", ".join(parts)

    return labels


def _shorten_solver_name(name: str) -> str:
    """Shorten solver name for plot labels."""
    # Remove common prefixes
    short = name.replace("PARTIAL_CONDENSING_", "PCOND ")
    short = short.replace("FULL_CONDENSING_", "FCOND ")
    return short


def plot_metric(
    metric: str,
    df: pandas.DataFrame,
    test_set: TestSet,
    solver_ids: Optional[List[str]] = None,
    labels: Optional[Dict[str, str]] = None,
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
    if labels is None:
        labels = {sid: sid for sid in plot_solver_ids}

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
