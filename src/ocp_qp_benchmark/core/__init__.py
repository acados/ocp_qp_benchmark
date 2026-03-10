"""Core benchmark components."""

from .runner import run, solve_problem
from .result import Result
from .test_set import TestSet
from .solver_set import (
    SolverSet,
)
from .supported_solvers import (
    ACADOS_OCP_QP_SOLVERS,
    ACADOS_CASADI_SOLVERS,
    EXTERNAL_SOLVERS
)
