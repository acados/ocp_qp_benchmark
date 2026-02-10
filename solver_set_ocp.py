"""Solver settings."""

from typing import Any, Dict, Iterator, Set

import numpy as np


class SolverSettings:
    """Settings for multiple solvers."""

    IMPLEMENTED_SOLVERS: Set[str] = set(
        [
        'PARTIAL_CONDENSING_HPIPM', 
        'FULL_CONDENSING_QPOASES', 
        'FULL_CONDENSING_HPIPM', 
        'PARTIAL_CONDENSING_QPDUNES',
        'PARTIAL_CONDENSING_OSQP', 
        'PARTIAL_CONDENSING_CLARABEL', 
        'FULL_CONDENSING_DAQP'
        ]
    )

    SOLVER_SETTINGS: Set[str] = set(
        [
        'default',
        ]
    )

    @staticmethod
    def is_complied(solver: str) -> bool:
        # TODO: check solver compliance
        return True

class SolverSet:
    def __init__(self, 
                 solvers: list[str] = SolverSettings.IMPLEMENTED_SOLVERS,
                 solver_settings: list[str] = SolverSettings.SOLVER_SETTINGS):

        candidate_solvers = set(
            solver 
            for solver in SolverSettings.IMPLEMENTED_SOLVERS 
            if solver in solvers)

        solvers = set(
            solver
            for solver in candidate_solvers
            if SolverSettings.is_complied(solver)
        )

        self.solvers = solvers
        self.solver_settings = solver_settings