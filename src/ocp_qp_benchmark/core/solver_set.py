"""Solver settings and configuration."""

import inspect
from typing import Union

from acados_template import AcadosOcpQpOptions
from acados_template.acados_code_gen_options import AcadosCodeGenOptions
from ocp_qp_benchmark.core.external import (
    ExternalQp,
    ExternalQpSolver,
    ExternalSolverConfig,
    load_external_class,
)
from ocp_qp_benchmark.core.supported_solvers import (
    ACADOS_OCP_QP_SOLVERS,
    ACADOS_CASADI_SOLVERS,
)
import json

class SolverSet:
    """Collection of solver configurations to benchmark."""

    def __init__(self, solver_list: list[dict]):
        """Initialize solver set.

        Args:
            solver_list: List of dictionaries mapping solver names to their configurations.
        """
        self.solver_list = solver_list
        self.solvers = []
        self.solver_ids = []
        with open(AcadosCodeGenOptions().acados_lib_path + '/link_libs.json', 'r') as f:
            self.link_lib_dict = json.load(f)
        self.link_lib_dict['hpipm'] = 'hpipm'  # hpipm is default and not in link_libs.json

        for solver_dict in self.solver_list:
            name = solver_dict.get("solver")
            opts = solver_dict.get("opts")
            if "qp_class" in solver_dict or "solver_class" in solver_dict:
                self._add_external_solver(
                    name, solver_dict.get("qp_class"), solver_dict.get("solver_class"), opts
                )
            elif name in ACADOS_OCP_QP_SOLVERS:
                self._add_acados_qp_solver(name, opts)
            elif name in ACADOS_CASADI_SOLVERS:
                self._add_acados_casadi_qp_solver(name, opts)
            else:
                raise ValueError(f"Unknown solver: {name}")
        self.solver_ids = [self._create_solver_id(opts) for opts in self.solvers]

    def __len__(self) -> int:
        return len(self.solvers)

    def __iter__(self):
        return iter(self.solvers)

    def _add_acados_qp_solver(self, name: str, opts: dict):
        '''
        Add an acados OCP QP solver configuration to the set.
        '''
        if self.check_compile(name):
            solver_opts = AcadosOcpQpOptions()
            solver_opts.qp_solver = name
            solver_opts.iter_max = opts.get("iter_max", 1000)
            for key, value in opts.items():
                if hasattr(solver_opts, key):
                    setattr(solver_opts, key, value)
                else:
                    raise ValueError(f"Unknown option: {key}")
            self.solvers.append(solver_opts)
        else:
            print(f"Skipping solver {name} due to missing dependencies.")

    def _add_acados_casadi_qp_solver(self, name: str, opts: dict):
        opts['qp_solver'] = name
        solver_opts = opts.copy()
        self.solvers.append(solver_opts)

    def _add_external_solver(self, name: str, qp_class, solver_class, opts: dict):
        '''
        Add an external solver configuration to the set.
        e.g., {"solver": "MY_SOLVER", "qp_class": "path/to/file.py:MyQp",
               "solver_class": "path/to/file.py:MySolver", "opts": {...}}
        '''
        if not name:
            raise ValueError(f"External solver {solver_class} needs a 'solver' name.")
        if name in ACADOS_OCP_QP_SOLVERS + ACADOS_CASADI_SOLVERS:
            raise ValueError(f"External solver name '{name}' clashes with a built-in solver name.")
        if qp_class is None or solver_class is None:
            raise ValueError(f"External solver '{name}' needs both 'qp_class' and 'solver_class'.")
        qp_cls = load_external_class(qp_class, ExternalQp)
        solver_cls = load_external_class(solver_class, ExternalQpSolver)
        self.solvers.append(ExternalSolverConfig(name, qp_cls, solver_cls, dict(opts or {})))

    def check_compile(self, name: str) -> bool:
        solver_name = name.lower().split("_")[-1]
        if self.link_lib_dict[solver_name] == '':
            return False
        return True

    def _create_solver_id(self, opts: Union[AcadosOcpQpOptions, dict, ExternalSolverConfig]) -> str:
        """
        Generate a unique identifier string from solver options.
        e.g., "PARTIAL_CONDENSING_OSQP_iter_max=500" for an AcadosOcpQpOptions with qp_solver="PARTIAL_CONDENSING_OSQP" and iter_max=500.

        Args:
            opts: Solver options object.

        Returns:
            Unique identifier string for this configuration.
        """
        if isinstance(opts, ExternalSolverConfig):
            return opts.name

        parts = [opts.get('qp_solver')]

        if isinstance(opts, AcadosOcpQpOptions):
            # Add non-default options to the ID
            default_opts = AcadosOcpQpOptions()

            # Get all properties of the class
            props = [name for name, value in inspect.getmembers(type(opts)) if isinstance(value, property)]

            for attr in props:
                opts_value = getattr(opts, attr)
                if attr == "qp_solver":
                    continue  # skip qp_solver in ID
                default_value = getattr(default_opts, attr)
                if opts_value != default_value:
                    parts.append(f"{attr}={opts_value}")

            return "_".join(parts)
        elif isinstance(opts, dict):
            return opts.get('qp_solver', 'UNKNOWN_SOLVER')
        else:
            raise ValueError('Unknown solver options type, expected AcadosOcpQpOptions, dict or ExternalSolverConfig')

    def get_solver_ids_by_names(self, names):
        ids = []
        for i in range(len(self.solver_ids)):
            for name in names:
                if name in self.solver_ids[i]:
                    ids.append(self.solver_ids[i])
        return ids

    def dump_configs_to_json(self, path: str):
        """Dump solver configurations to a JSON file for record-keeping."""
        raise NotImplementedError("Dumping solver configs to JSON not implemented yet")