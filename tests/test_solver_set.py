"""Tests for solver set."""

import pytest

from ocp_qp_benchmark.core import SolverSet, SolverSettings


def test_solver_settings_implemented_solvers():
    """Test that implemented solvers set is not empty."""
    assert len(SolverSettings.IMPLEMENTED_SOLVERS) > 0


def test_solver_set_default():
    """Test SolverSet with default parameters."""
    solver_set = SolverSet()
    assert len(solver_set.solvers) > 0
    assert len(solver_set.solver_settings) > 0


def test_solver_set_filter():
    """Test SolverSet filters to only implemented solvers."""
    solver_set = SolverSet(
        solvers=["FULL_CONDENSING_HPIPM", "NONEXISTENT_SOLVER"]
    )
    assert "FULL_CONDENSING_HPIPM" in solver_set.solvers
    assert "NONEXISTENT_SOLVER" not in solver_set.solvers
