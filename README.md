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

## Supported Solvers

- `PARTIAL_CONDENSING_HPIPM`
- `FULL_CONDENSING_HPIPM`
- `FULL_CONDENSING_QPOASES`
- `FULL_CONDENSING_DAQP`
- `PARTIAL_CONDENSING_OSQP`
- `PARTIAL_CONDENSING_CLARABEL`
