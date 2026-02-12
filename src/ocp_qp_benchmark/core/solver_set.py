"""Solver settings."""

from typing import Set


class SolverSettings:
    """Settings for multiple solvers."""

    IMPLEMENTED_SOLVERS: Set[str] = set(
        [
            "PARTIAL_CONDENSING_HPIPM",
            "FULL_CONDENSING_QPOASES",
            "FULL_CONDENSING_HPIPM",
            "PARTIAL_CONDENSING_QPDUNES",
            "PARTIAL_CONDENSING_OSQP",
            "PARTIAL_CONDENSING_CLARABEL",
            "FULL_CONDENSING_DAQP",
        ]
    )

    SOLVER_SETTINGS: Set[str] = set(
        [
            "default",
        ]
    )

    @staticmethod
    def is_compiled(solver: str) -> bool:
        # TODO: check solver compliance
        return True


class SolverSet:
    def __init__(
        self,
        solvers: list[str] = None,
        solver_settings: list[str] = None,
    ):
        if solvers is None:
            solvers = list(SolverSettings.IMPLEMENTED_SOLVERS)
        if solver_settings is None:
            solver_settings = list(SolverSettings.SOLVER_SETTINGS)

        candidate_solvers = set(
            solver
            for solver in SolverSettings.IMPLEMENTED_SOLVERS
            if solver in solvers
        )

        solvers = set(
            solver
            for solver in candidate_solvers
            if SolverSettings.is_compiled(solver)
        )

        self.solvers = solvers
        self.solver_settings = solver_settings
