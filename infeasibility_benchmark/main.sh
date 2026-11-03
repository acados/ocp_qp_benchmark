ocp-benchmark run -c infeasibility_benchmark.json --results results/qpbenchmark_results.csv
ocp-benchmark plot --results results/qpbenchmark_results.csv --metric runtime_external
ocp-benchmark plot --results results/qpbenchmark_results.csv --metric runtime_fair

ocp-benchmark status-table --results results/qpbenchmark_results.csv
