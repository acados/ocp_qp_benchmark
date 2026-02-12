"""Tests for solver set."""

import pytest

from ocp_qp_benchmark.core import (
    SolverSet,
    create_solver_options,
    get_solver_id,
)

def test_create_solver_options():
    """Test creating solver options."""
    opts = create_solver_options("FULL_CONDENSING_HPIPM")
    assert opts.qp_solver == "FULL_CONDENSING_HPIPM"
    assert opts.iter_max == 1000


def test_create_solver_options_with_kwargs():
    """Test creating solver options with custom kwargs."""
    opts = create_solver_options(
        "FULL_CONDENSING_HPIPM",
        tol_stat=1e-10,
    )
    assert opts.qp_solver == "FULL_CONDENSING_HPIPM"
    assert opts.tol_stat == 1e-10


def test_get_solver_id_default():
    """Test solver ID for default options."""
    opts = create_solver_options("FULL_CONDENSING_HPIPM")
    solver_id = get_solver_id(opts)
    assert solver_id == "FULL_CONDENSING_HPIPM"


def test_get_solver_id_with_custom_options():
    """Test solver ID includes non-default options."""
    opts = create_solver_options(
        "FULL_CONDENSING_HPIPM",
        tol_stat=1e-10,
    )
    solver_id = get_solver_id(opts)
    assert "FULL_CONDENSING_HPIPM" in solver_id
    assert "tol_stat" in solver_id


def test_solver_set():
    """Test SolverSet creation and iteration."""
    solvers = [
        create_solver_options("FULL_CONDENSING_HPIPM"),
        create_solver_options("FULL_CONDENSING_DAQP"),
    ]
    solver_set = SolverSet(solvers)
    assert len(solver_set) == 2

    solver_list = list(solver_set)
    assert len(solver_list) == 2


def test_solver_set_from_names():
    """Test SolverSet.from_solver_names factory."""
    solver_set = SolverSet.from_solver_names(
        ["FULL_CONDENSING_HPIPM", "FULL_CONDENSING_DAQP"]
    )
    assert len(solver_set) == 2
