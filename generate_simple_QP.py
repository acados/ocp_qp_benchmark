import numpy as np
import os
from utils import convert_npz_to_json
from pathlib import Path

def generate_problems(num_problems: int,
                      horizon: int,
                      nx: int,
                      nu: int,
                      output_dir:str):

    print(f"Generating {num_problems} QP problems in {output_dir}...")

    for i in range(num_problems):

        # Simple Dynamics: x_{k+1} = A x_k + B u_k
        # Generating LTI system for simplicity
        A = np.random.randn(nx, nx)
        # Normalize spectral radius to be around 1 for stability
        # This prevents the states from exploding over the horizon
        spectral_radius = np.max(np.abs(np.linalg.eigvals(A)))
        if spectral_radius > 0:
            A = A / spectral_radius

        B = np.random.randn(nx, nu)

        # Cost function: sum(0.5 * x_k^T Q x_k + 0.5 * u_k^T R u_k) + 0.5 * x_N^T Q_N x_N
        # Q >= 0, R > 0
        # Generate random positive semidefinite Q
        Q_temp = np.random.randn(nx, nx)
        Q = Q_temp.T @ Q_temp
        Q = Q / np.linalg.norm(Q) # Normalize

        # Generate random positive definite R
        R_temp = np.random.randn(nu, nu)
        R = R_temp.T @ R_temp + 1e-2 * np.eye(nu) # Add regularization
        R = R / np.linalg.norm(R) # Normalize

        # Store matrices
        # We store the LTI matrices. If time-varying is needed, these can be replicated.
        filename = os.path.join(output_dir, f'prob_{i}.npz')
        np.savez(
            filename,
            A=A,
            B=B,
            Q=Q,
            R=R,
            N=horizon,
        )
        print(f"Generated {filename}: nx={nx}, nu={nu}, N={horizon}")

if __name__ == "__main__":
    num_problems = 10
    horizon = 20
    nx = 10
    nu = 2
    set_name = f"{horizon}_{nx}*{nu}_Problem_set"
    output_dir = 'data/' + set_name
    os.makedirs(output_dir, exist_ok=True)

    np.random.seed(42) # For reproducibility
    generate_problems(num_problems, horizon, nx, nu, output_dir)

    # Convert generated .npz files to .json format
    input_dir = output_dir
    output_dir = output_dir
    # Get all .npz files
    npz_files = sorted(Path(input_dir).glob('*.npz'))
    print(f"Found {len(npz_files)} .npz files to convert\n")
    # Convert each file
    for npz_file in npz_files:
        convert_npz_to_json(str(npz_file), output_dir)
    print("Conversion complete!")


    # # check sample problem
    # set_name = '20_10*2_Problem_set'
    # file_path = 'data/' + set_name + '/prob_0.npz'
    # data = np.load(file_path)
    # print(f"Sample problem loaded from {file_path}:")
    # print(f"A: {data['A']}")
    # print(f"B: {data['B']}")
    # print(f"Q: {data['Q']}")
    # print(f"R: {data['R']}")

    # from problem_ocp import parametric_QP_Problem
    # from acados_template import AcadosOcpSolver
    # ocp_problem = parametric_QP_Problem(
    #     N=20,
    #     nx=10,
    #     nu=2,
    #     solver='PARTIAL_CONDENSING_HPIPM',
    #     settings='default',
    # )
    # ocp_problem.populate_manager('data/20_10*2_Problem_set/prob_0.json')
    # print("Sample problem populated from data/20_10*2_Problem_set/prob_0.json")
    # ocp_solver = AcadosOcpSolver(ocp_problem.ocp, verbose=True)
    # for i in range(ocp_problem.ocp.solver_options.N_horizon + 1):
    #     param_value = ocp_problem.param_manager.get_p_stagewise_values(i)
    #     ocp_solver.set(i, 'p', param_value)
    # status = ocp_solver.solve()
    # print(f"Solve status: {status}")
    # ocp_solver.print_statistics()