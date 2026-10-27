from typing import Literal, get_args

AcadosQpSolvers = Literal[
    "PARTIAL_CONDENSING_OSQP",
    "PARTIAL_CONDENSING_HPIPM",
    "PARTIAL_CONDENSING_CLARABEL",
    "FULL_CONDENSING_QPOASES",
    "FULL_CONDENSING_HPIPM",
    "FULL_CONDENSING_DAQP",
]

AcadosCasadiSolvers = Literal['IPOPT']

ACADOS_OCP_QP_SOLVERS = list(get_args(AcadosQpSolvers))
ACADOS_CASADI_SOLVERS = list(get_args(AcadosCasadiSolvers))
