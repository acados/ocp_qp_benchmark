ocp-benchmark run -c overhead_bm.json --results results/overhead_results.csv
ocp-benchmark plot --results results/overhead_results.csv --metric runtime_fair
ocp-benchmark plot --results results/overhead_results.csv --metric runtime_external

ocp-benchmark status-table --results results/overhead_results.csv
