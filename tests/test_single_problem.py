import zstandard as zstd
import json

from acados_template import AcadosOcpQp, AcadosOcpQpSolver, AcadosOcpQpOptions


def decompress(zstd_path) -> None:
    """
    Decompress a zstd compressed json file.

    Args:
        zstd_path: Path to the zstd compressed json file.
    """
    dctx = zstd.ZstdDecompressor()
    with open(zstd_path, 'rb') as f:
        decompressed_data = dctx.decompress(f.read())
        json_data = json.loads(decompressed_data.decode('utf-8'))
    return json_data

def main(problem_path, qp_solver_name):
    """
    Self-contained Quick test for specific problem with specific solver and options
    """

    # read json data
    if problem_path.endswith(".json.zst"):
        data = decompress(problem_path)
    elif problem_path.endswith(".json"):
        with open(problem_path, 'r') as f:
            data = json.load(f)
    else:
        raise ValueError(f"Unsupported file format for problem data: {problem_path}")

    qp = AcadosOcpQp.from_json(json_data=data)
    solver_options = AcadosOcpQpOptions()
    solver_options.qp_solver = qp_solver_name

    solver = AcadosOcpQpSolver(qp, solver_options)
    stats = solver.solve()
    iter = solver.get_stats("iter")
    print(f"{qp_solver_name} solved in {iter} iterations with status {stats}")

if __name__ == "__main__":
    # Assign the path to the specific problem
    problem_path = "ocp_qp_dataset_collection/random_qp/prob_0/prob_0.json.zst"

    # Assign the specific solver you want to test
    qp_sovler_name = "PARTIAL_CONDENSING_HPIPM"

    # Run the main function with the specified problem and solver
    main(problem_path, qp_sovler_name)