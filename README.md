# OCP QP Benchmark

Benchmarking framework for OCP QP solvers using [acados](https://github.com/acados/acados).

## Installation

```bash
pip install -e .
```

## Usage

### Run benchmark

```bash
ocp-benchmark
```

### Add problems to dataset

```bash
add-problems /path/to/json/folder --name my_dataset
```

### Python API

```python
from acados_template import AcadosOcpQpOptions
from ocp_qp_benchmark.core import TestSet, SolverSet, Results, run, create_solver_options
from ocp_qp_benchmark.visualization import plot_metric, generate_labels

# Create solver configurations
solvers = [
    create_solver_options("FULL_CONDENSING_HPIPM"),
    create_solver_options("FULL_CONDENSING_HPIPM", tol_stat=1e-10),  # Custom tolerance
    create_solver_options("FULL_CONDENSING_DAQP"),
]

# Create test set from problem folders
test_set = TestSet(qp_folder_paths=["ocp_qp_dataset_collection/random_qp/prob_0"])

# Run benchmark
solver_set = SolverSet(solvers)
results = Results(file_path="results/results.csv", test_set=test_set)
run(test_set, solver_set, results)

# Generate labels (auto-detects differing options)
labels = generate_labels(solvers)

# Plot results
plot_metric(metric="runtime_fair", df=results.df, test_set=test_set, labels=labels)
```

## Supported Solvers

- `PARTIAL_CONDENSING_HPIPM`
- `FULL_CONDENSING_HPIPM`
- `FULL_CONDENSING_QPOASES`
- `FULL_CONDENSING_DAQP`
- `PARTIAL_CONDENSING_OSQP`
- `PARTIAL_CONDENSING_CLARABEL`
