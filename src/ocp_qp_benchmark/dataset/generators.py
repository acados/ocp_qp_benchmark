"""QP problem generators."""

import os
from pathlib import Path

import numpy as np

from .converters import convert_npz_to_json


def generate_problems(
    num_problems: int,
    horizon: int,
    nx: int,
    nu: int,
    output_dir: str,
    seed: int = None,
) -> list[str]:
    """Generate random QP problems.

    Args:
        num_problems: Number of problems to generate.
        horizon: Prediction horizon N.
        nx: Number of states.
        nu: Number of controls.
        output_dir: Output directory for generated problems.
        seed: Random seed for reproducibility.

    Returns:
        List of paths to generated problem files.
    """
    print(f"Generating {num_problems} QP problems in {output_dir}...")

    if seed is not None:
        np.random.seed(seed)

    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

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

        # Cost function: sum(0.5 * x_k^T Q x_k + 0.5 * u_k^T R u_k)
        #                + 0.5 * x_N^T Q_N x_N
        # Q >= 0, R > 0
        # Generate random positive semidefinite Q
        Q_temp = np.random.randn(nx, nx)
        Q = Q_temp.T @ Q_temp
        Q = Q / np.linalg.norm(Q)  # Normalize

        # Generate random positive definite R
        R_temp = np.random.randn(nu, nu)
        R = R_temp.T @ R_temp + 1e-2 * np.eye(nu)  # Add regularization
        R = R / np.linalg.norm(R)  # Normalize

        # Store matrices
        filename = os.path.join(output_dir, f"prob_{i}.npz")
        np.savez(
            filename,
            A=A,
            B=B,
            Q=Q,
            R=R,
            N=horizon,
        )
        generated_files.append(filename)
        print(f"Generated {filename}: nx={nx}, nu={nu}, N={horizon}")

    return generated_files


def generate_and_convert_problems(
    num_problems: int,
    horizon: int,
    nx: int,
    nu: int,
    output_dir: str,
    seed: int = None,
) -> list[str]:
    """Generate random QP problems and convert to JSON format.

    Args:
        num_problems: Number of problems to generate.
        horizon: Prediction horizon N.
        nx: Number of states.
        nu: Number of controls.
        output_dir: Output directory for generated problems.
        seed: Random seed for reproducibility.

    Returns:
        List of paths to generated JSON files.
    """
    # Generate NPZ files
    npz_files = generate_problems(
        num_problems, horizon, nx, nu, output_dir, seed
    )

    # Convert to JSON
    json_files = []
    for npz_file in npz_files:
        json_path = convert_npz_to_json(npz_file, output_dir)
        json_files.append(json_path)

    print("Conversion complete!")
    return json_files
