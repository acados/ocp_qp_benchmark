from typing import Literal, get_args

AcadosQPSolver = Literal[
    "PARTIAL_CONDENSING_OSQP",
    "PARTIAL_CONDENSING_HPIPM",
    "PARTIAL_CONDENSING_CLARABEL",
    "FULL_CONDENSING_QPOASES",
    "FULL_CONDENSING_HPIPM",
    "FULL_CONDENSING_DAQP",
]

AcadosCasadiSolver = Literal['IPOPT']

External_solvers = Literal[
    None # placeholder for future external solvers
]

ACADOS_OCP_QP_SOLVERS = list(get_args(AcadosQPSolver))
ACADOS_CASADI_SOLVERS = list(get_args(AcadosCasadiSolver))
EXTERNAL_SOLVERS = list(get_args(External_solvers))