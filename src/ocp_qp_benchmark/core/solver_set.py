"""Solver settings and configuration."""

import inspect
from typing import List

from acados_template import AcadosOcpQpOptions


def get_solver_id(opts: AcadosOcpQpOptions) -> str:
    """Generate a unique identifier string from solver options.

    This ID is used to store results in CSV and identify solver configurations.

    Args:
        opts: Solver options object.

    Returns:
        Unique identifier string for this configuration.
    """
    parts = [opts.qp_solver]

    # Add non-default options to the ID
    default_opts = AcadosOcpQpOptions()

    # Get all properties of the class
    props = [name for name, value in inspect.getmembers(type(opts)) if isinstance(value, property)]
    
    for attr in props:
        opts_value = getattr(opts, attr)
        default_value = getattr(default_opts, attr)
        if opts_value != default_value:
            parts.append(f"{attr}={opts_value}")

    return "_".join(parts)


def create_solver_options(
    qp_solver: str,
    print_level: int = 0,
    iter_max: int = 1000,
    **kwargs,
) -> AcadosOcpQpOptions:
    """Create solver options with common defaults.

    Args:
        qp_solver: Name of the QP solver.
        print_level: Verbosity level.
        iter_max: Maximum iterations.
        **kwargs: Additional options to set.

    Returns:
        Configured AcadosOcpQpOptions object.
    """
    opts = AcadosOcpQpOptions()
    opts.qp_solver = qp_solver
    opts.print_level = print_level
    opts.iter_max = iter_max

    for key, value in kwargs.items():
        if hasattr(opts, key):
            setattr(opts, key, value)
        else:
            raise ValueError(f"Unknown option: {key}")

    return opts


class SolverSet:
    """Collection of solver configurations to benchmark."""

    def __init__(self, solvers: List[AcadosOcpQpOptions]):
        """Initialize solver set.

        Args:
            solvers: List of solver option configurations.
        """
        self.solvers = solvers

    def __len__(self) -> int:
        return len(self.solvers)

    def __iter__(self):
        return iter(self.solvers)

    @staticmethod
    def from_solver_names(
        solver_names: List[str],
        print_level: int = 0,
        iter_max: int = 1000,
    ) -> "SolverSet":
        """Create a SolverSet from a list of solver names with default options.

        Args:
            solver_names: List of QP solver names.
            print_level: Verbosity level for all solvers.
            iter_max: Maximum iterations for all solvers.

        Returns:
            SolverSet with default configurations.
        """
        solvers = [
            create_solver_options(name, print_level=print_level, iter_max=iter_max)
            for name in solver_names
        ]
        return SolverSet(solvers)
