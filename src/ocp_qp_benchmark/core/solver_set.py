"""Solver settings and configuration."""

import inspect
from typing import List, Union

from acados_template import AcadosOcpQpOptions
from acados_template.acados_code_gen_opts import AcadosCodeGenOpts
import json

ACADOS_OCP_QP_SOLVERS = [
    "PARTIAL_CONDENSING_OSQP",
    "PARTIAL_CONDENSING_HPIPM",
    "PARTIAL_CONDENSING_CLARABEL",
    "FULL_CONDENSING_QPOASES",
    "FULL_CONDENSING_HPIPM",
    "FULL_CONDENSING_DAQP",
]

ACADOS_CASADI_SOLVERS = [
    'IPOPT'
]

EXTERNAL_SOLVERS = [

]

class SolverSet:
    """Collection of solver configurations to benchmark."""

    def __init__(self, solver_dicts: tuple[dict[str, dict]]):
        """Initialize solver set.

        Args:
            solver_dict: Dictionary mapping solver names to their configurations.
        """
        self.solver_dicts = solver_dicts
        self.solvers = []
        self.solver_ids = []
        with open(AcadosCodeGenOpts().acados_lib_path + '/link_libs.json', 'r') as f:
            self.link_lib_dict = json.load(f)
        self.link_lib_dict['hpipm'] = 'hpipm'  # hpipm is default and not in link_libs.json

        for solver_dict in self.solver_dicts:
            name = list(solver_dict.keys())[0]
            opts = list(solver_dict.values())[0]
            if name in ACADOS_OCP_QP_SOLVERS:
                self._add_acados_qp_solver(name, opts)
            elif name in ACADOS_CASADI_SOLVERS:
                self._add_acados_casadi_qp_solver(name, opts)
            elif name in EXTERNAL_SOLVERS:
                self._add_external_solver(name, opts)
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
        raise NotImplementedError(f"Casadi solvers not implemented yet")

    def _add_external_solver(self, name: str, opts: dict):
        raise NotImplementedError(f"External solvers not implemented yet")

    def check_compile(self, name: str) -> bool:
        solver_name = name.lower().split("_")[-1]
        if self.link_lib_dict[solver_name] == '':
            return False
        return True

    def _create_solver_id(self, opts: Union[AcadosOcpQpOptions, dict]) -> str:
        """
        Generate a unique identifier string from solver options.
        e.g., "PARTIAL_CONDENSING_OSQP_iter_max=500" for an AcadosOcpQpOptions with qp_solver="PARTIAL_CONDENSING_OSQP" and iter_max=500.

        Args:
            opts: Solver options object.

        Returns:
            Unique identifier string for this configuration.
        """
        parts = [opts.qp_solver]

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
            raise NotImplementedError("get_solver_id for dict options not implemented yet")

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