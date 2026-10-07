"""Interfaces for plugging external QP solvers into the benchmark."""

import importlib
import importlib.util
import inspect
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from acados_template import AcadosOcpQp, AcadosOcpIterate


class ExternalQp(ABC):
    """QP in an external solver's format, adapted from a benchmark problem."""

    @classmethod
    @abstractmethod
    def from_acados_qp(cls, qp: AcadosOcpQp) -> "ExternalQp":
        """Build the QP from a benchmark problem.

        Raise NotImplementedError for unsupported problem features (e.g. slacks, masks);
        the runner then records the problem as failed for this solver.
        """

    @classmethod
    def from_json(cls, json_data: dict) -> "ExternalQp":
        """Build the QP from benchmark JSON data."""
        return cls.from_acados_qp(AcadosOcpQp.from_json(json_data=json_data))

    def to_iterate(self, *solution) -> Optional[AcadosOcpIterate]:
        """Map a native solution back to the acados iterate layout.

        Optional, only needed to compare against reference solutions (compare_sol).
        """
        return None


class ExternalQpSolver(ABC):
    """External solver, mirroring the interface of the acados QP solvers.

    It receives the QP built by the ExternalQp class configured in the same solver entry.
    The runner times only solve(), so __init__ should be limited to format conversion
    and allocation; factorizations belong in solve() to keep runtimes comparable.
    """

    def __init__(self, qp: ExternalQp, opts: dict):
        self.qp = qp
        self.opts = opts

    @abstractmethod
    def solve(self) -> int:
        """Solve the QP and return the status, 0 on success."""

    @abstractmethod
    def get_stats(self, field: str) -> Union[int, float]:
        """Return a statistic of the last solve: 'iter' (int) or 'time_tot' (float, seconds)."""

    def get_iterate(self) -> Optional[AcadosOcpIterate]:
        """Return the last solution as an AcadosOcpIterate, or None to skip comparison."""
        return None


@dataclass
class ExternalSolverConfig:
    """Entry of a SolverSet for an external solver."""

    name: str
    qp_cls: type[ExternalQp]
    solver_cls: type[ExternalQpSolver]
    opts: dict = field(default_factory=dict)


def load_external_class(spec: Union[str, type], base_cls: type) -> type:
    """Resolve an external QP or solver class.

    Args:
        spec: 'package.module:ClassName', 'path/to/file.py:ClassName' or the class itself.
        base_cls: Base class the result must implement (ExternalQp or ExternalQpSolver).

    Returns:
        The validated subclass of base_cls.
    """
    if isinstance(spec, str):
        module_ref, _, class_name = spec.rpartition(":")
        if not module_ref or not class_name:
            raise ValueError(
                f"Expected 'module:ClassName' or 'path/to/file.py:ClassName', got: {spec}"
            )
        if module_ref.endswith(".py"):
            module = _load_module_from_file(Path(module_ref))
        else:
            module = importlib.import_module(module_ref)
        cls = getattr(module, class_name)
    else:
        cls = spec

    if not (isinstance(cls, type) and issubclass(cls, base_cls)):
        raise TypeError(f"{spec} is not a subclass of {base_cls.__name__}")
    if inspect.isabstract(cls):
        raise TypeError(f"{cls.__name__} does not implement all abstract methods")
    return cls


def _load_module_from_file(path: Path):
    """Import a Python file as a module, reusing it if it was already loaded."""
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"External solver file not found: {path}")
    module_name = f"ocp_qp_benchmark_external_{path.stem}"
    module = sys.modules.get(module_name)
    if module is not None and Path(module.__file__).resolve() == path:
        return module
    module_spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    module_spec.loader.exec_module(module)
    return module
