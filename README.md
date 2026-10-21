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

### Run benchmark

```bash
ocp-benchmark run -c tests/benchmark.json
```

By default, results are written to `results/qpbenchmark_results.csv`. Choose another
CSV or Parquet output path with `--results`:

```bash
ocp-benchmark run -c tests/benchmark.json --results results/run-01.parquet
```

Configuration keys (example: [tests/benchmark.json](tests/benchmark.json)):

| Key | Description |
| --- | --- |
| `test_setting` | Datasets in `ocp_qp_dataset_collection/`, e.g. `["random_qp"]` |
| `test_filter_setting` | Filters on the problem `meta.json`, e.g. `[{"has_slacks": false}]` |
| `test_description` | Label used in plots |
| `solver_setting` | List of `{"solver": <name>, "opts": {...}}`; a solver may appear several times with different options. External solvers also need `qp_class` and `solver_class`, see [Connect your own solver](#connect-your-own-solver) |
| `compare_sol` | Compare solutions with the reference solution (default: `false`) |

The `run` command only runs solvers and writes results. Plotting can be repeated later
from the saved file, without rerunning the benchmark:

```bash
ocp-benchmark plot --results results/qpbenchmark_results.csv
ocp-benchmark plot --results results/run-01.parquet \\
    --metric runtime_fair \\
    --solver-ids PARTIAL_CONDENSING_HPIPM FULL_CONDENSING_HPIPM \\
    --output figures/hpipm-runtime.pdf
```

If `--solver-ids` is omitted, all solver IDs in the results file are plotted. IDs must
match the `solver` column exactly. The default metric is `runtime_fair`; the default
plot path is `figures/<results-file>_<metric>.pdf`.

### Add problems to dataset

```bash
add-problems /path/to/json/folder --name my_dataset_name
```

Each `.json` file must be loadable by `AcadosOcpQp.from_json()`. Problems are added to `ocp_qp_dataset_collection/my_dataset_name/` (default name: the folder name), each with:

- `<problem>.json.zst`: compressed QP data
- `<problem>_meta.json`: problem properties (`N`, `has_slacks`, `has_masks`, `definiteness`, ...), used by `test_filter_setting`
- `<problem>_ref_sol.json.zst`: IPOPT reference solution (omitted if IPOPT fails)

### Python API

See [src/ocp_qp_benchmark/cli/main.py](src/ocp_qp_benchmark/cli/main.py) for an example using `TestSet`, `SolverSet`, `Results` and `run` directly.

## Supported Solvers

- `PARTIAL_CONDENSING_HPIPM`
- `FULL_CONDENSING_HPIPM`
- `FULL_CONDENSING_QPOASES`
- `FULL_CONDENSING_DAQP`
- `PARTIAL_CONDENSING_OSQP`
- `PARTIAL_CONDENSING_CLARABEL`
- `IPOPT` (via CasADi; also used to generate reference solutions)

Other solvers can be connected with an adapter, see [Connect your own solver](#connect-your-own-solver).

### Connect your own solver

Write an adapter file with two classes:

- an `ExternalQp` subclass, which converts a benchmark problem (`AcadosOcpQp`) into your solver's QP format;
- an `ExternalQpSolver` subclass, which runs your solver on that QP.

Template, with `my_solver`, `MySolverQp` and `MySolverImpl` as placeholders for your solver:

```python
import sys

from acados_template import AcadosOcpIterate
from ocp_qp_benchmark.core import ExternalQp, ExternalQpSolver

sys.path.insert(0, "/path/to/my_solver_repo")  # only if your solver is not installed
from my_solver import MySolverQp, MySolverImpl


class MyQp(ExternalQp):
    def __init__(self, data):
        self.data = data

    @classmethod
    def from_acados_qp(cls, qp):
        if qp.has_slacks():
            raise NotImplementedError("slacks are not supported")
        # TODO: build your QP from qp.N, qp.dims and the per-stage lists qp.A, qp.B, qp.Q, qp.lbx, ...
        return cls(MySolverQp(...))

    def to_iterate(self, solution):
        # TODO: map your solution to the acados conventions
        return AcadosOcpIterate(x=..., u=..., z=..., sl=..., su=..., pi=..., lam=...)


class MySolver(ExternalQpSolver):
    def __init__(self, qp, opts):
        super().__init__(qp, opts)
        self.solver = MySolverImpl(qp.data, **opts)

    def solve(self):
        try:
            self.status = self.solver.solve()
        except Exception:
            self.status = 4  # an uncaught exception stops the benchmark
        return self.status

    def get_stats(self, field):
        if field == "iter":
            return self.solver.iter_count
        if field == "time_tot":
            return self.solver.solve_time

    def get_iterate(self):
        if self.status != 0:
            return None
        return self.qp.to_iterate(self.solver.solution)
```

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