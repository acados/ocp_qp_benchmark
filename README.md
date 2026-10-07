# OCP QP Benchmark

Benchmarking framework for OCP QP solvers using [acados](https://github.com/acados/acados).

## Installation

```bash
git clone https://github.com/acados/ocp_qp_benchmark.git
cd ocp_qp_benchmark
git submodule update --recursive --init
pip install -e .
```

## Usage

Run the commands from the repository root, since the dataset collection `ocp_qp_dataset_collection/` is resolved relative to the working directory.

### Run benchmark

```bash
ocp-benchmark -c tests/benchmark.json
```

The configuration JSON has the following keys (see [tests/benchmark.json](tests/benchmark.json) for an example):

| Key | Description |
| --- | --- |
| `test_setting` | Dataset names under `ocp_qp_dataset_collection/` to run, e.g. `["random_qp"]` |
| `test_filter_setting` | Keep only problems whose `meta.json` matches, e.g. `[{"has_slacks": false}]` |
| `test_description` | Label for the test set, used in plots |
| `solver_setting` | List of `{"solver": <name>, "opts": {...}}`; the same solver can appear with different options. Solvers connected with an adapter also need `"qp_class"` and `"solver_class"` keys, see [Connect your own solver](#connect-your-own-solver) |
| `eval_solver_names` | Subset of solvers to plot in a second, focused figure |
| `metric` | Metric to plot (default: `runtime_fair`) |
| `compare_sol` | Compare solutions against the reference solution (default: `false`) |

Results are written to `results/qpbenchmark_results.csv` and plots to `figures/`.

### Connect your own solver

Any QP solver can be benchmarked without changing this package: you write an adapter, a Python file that can live next to your solver, with two classes, and name both in the configuration JSON:

- an `ExternalQp` subclass, which converts a benchmark problem (an `AcadosOcpQp`) into your solver's QP format;
- an `ExternalQpSolver` subclass, which calls your solver on that QP.


**1. Write the adapter**, e.g. `benchmark_adapter.py` next to your solver. 
To use the following template, fill in the `TODO`s, or just text your coding agent.

`my_solver`, `MySolverQp` and `MySolverImpl` stand for your solver's module, QP format and solver.

```python
import sys

from acados_template import AcadosOcpIterate
from ocp_qp_benchmark.core import ExternalQp, ExternalQpSolver

sys.path.insert(0, "/path/to/my_solver_repo")  # only if your solver is not installed
from my_solver import MySolverQp, MySolverImpl


class MyQp(ExternalQp):
    """Your solver's QP, built from a benchmark problem."""

    def __init__(self, data):
        self.data = data

    @classmethod
    def from_acados_qp(cls, qp):
        if qp.has_slacks():
            raise NotImplementedError("slacks are not supported")  # recorded as failed
        # TODO: build your QP from qp.N, qp.dims and the per-stage lists qp.A, qp.B, qp.Q, qp.lbx, ...
        return cls(MySolverQp(...))

    def to_iterate(self, solution):
        # TODO: map your solution to the acados conventions listed below
        return AcadosOcpIterate(x=..., u=..., z=..., sl=..., su=..., pi=..., lam=...)


class MySolver(ExternalQpSolver):
    """Calls your solver on a MyQp."""

    def __init__(self, qp, opts):
        super().__init__(qp, opts)
        self.solver = MySolverImpl(qp.data, **opts)

    def solve(self):
        try:
            self.status = self.solver.solve()
        except Exception:
            self.status = 4  # an uncaught exception would stop the whole benchmark
        return self.status

    def get_stats(self, field):
        if field == "iter":
            return self.solver.iter_count
        if field == "time_tot":
            return self.solver.solve_time

    def get_iterate(self):
        if self.status != 0:
            return None  # compare converged solutions only
        return self.qp.to_iterate(self.solver.solution)
```

| Member | Required | Description |
| --- | --- | --- |
| `ExternalQp.from_acados_qp(qp)` | yes | Build your QP from the benchmark problem. Raising `NotImplementedError` (or any error) records the problem as failed (status `-1`) for this solver, and the run continues |
| `ExternalQp.to_iterate(...)` | no | Helper for `get_iterate()` that maps your solution to an `AcadosOcpIterate`; the benchmark does not call it |
| `ExternalQpSolver.__init__(qp, opts)` | no | Receives the QP built by the entry's `qp_class` and the `opts` from the config; call `super().__init__(qp, opts)` |
| `solve()` | yes | Solve and return the status: `0` on success, otherwise preferably an acados code (`1` NaN, `2` maximum iterations, `3` minimal step, `4` QP failure). Only `0` counts as solved in the plots |
| `get_stats(field)` | yes | `"iter"`: iteration count, `"time_tot"`: solver-reported time in seconds |
| `get_iterate()` | no | Solution as an `AcadosOcpIterate`, used by `compare_sol`. Returning `None` (the default) skips the comparison |


**2. Add the solver to the configuration JSON** with `"qp_class"` and `"solver_class"` keys:

```json
"solver_setting": [
    {"solver": "PARTIAL_CONDENSING_HPIPM", "opts": {}},
    {
        "solver": "MY_SOLVER",
        "qp_class": "/path/to/benchmark_adapter.py:MyQp",
        "solver_class": "/path/to/benchmark_adapter.py:MySolver",
        "opts": {"max_iter": 100}
    }
]
```

**3. Run the benchmark** from the repository root:

```bash
ocp-benchmark -c my_config.json
```

### Add problems to dataset

```bash
add-problems /path/to/json/folder --name my_dataset_name
```

Each `.json` file in the folder must be loadable by `AcadosOcpQp.from_json()`. The problems are added to `ocp_qp_dataset_collection/my_dataset_name/` (default name: the folder name). Each problem gets:

- `<problem>.json.zst`: compressed QP data
- `<problem>_meta.json`: problem properties (`N`, `has_slacks`, `has_masks`, `definiteness`, ...), used by `test_filter_setting`
- `<problem>_ref_sol.json.zst`: reference solution from IPOPT (omitted if IPOPT fails)

### Python API

See [src/ocp_qp_benchmark/cli/main.py](src/ocp_qp_benchmark/cli/main.py) for an example of using `TestSet`, `SolverSet`, `Results` and `run` directly.

## Supported Solvers

- `PARTIAL_CONDENSING_HPIPM`
- `FULL_CONDENSING_HPIPM`
- `FULL_CONDENSING_QPOASES`
- `FULL_CONDENSING_DAQP`
- `PARTIAL_CONDENSING_OSQP`
- `PARTIAL_CONDENSING_CLARABEL`
- `IPOPT` (via CasADi; also used to generate reference solutions)

Other solvers can be connected with an adapter, see [Connect your own solver](#connect-your-own-solver).
