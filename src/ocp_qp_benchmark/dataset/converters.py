"""Data format converters."""

import os
from pathlib import Path

import numpy as np


def convert_npz_to_json(npz_path: str, output_dir: str) -> str:
    """Convert NPZ file to JSON format for acados.

    Args:
        npz_path: Path to the NPZ file.
        output_dir: Output directory for the JSON file.

    Returns:
        Path to the generated JSON file.
    """
    # This is a placeholder - the actual implementation depends on
    # the acados JSON format requirements
    data = np.load(npz_path)

    # Extract problem data
    A = data["A"]
    B = data["B"]
    Q = data["Q"]
    R = data["R"]
    N = int(data["N"])

    # TODO: Implement actual conversion to acados OCP QP JSON format
    # This requires creating the full OCP QP structure with:
    # - Dynamics matrices for each stage
    # - Cost matrices for each stage
    # - Constraints (if any)

    output_path = os.path.join(
        output_dir, Path(npz_path).stem + ".json"
    )

    # Placeholder: actual implementation would use acados_template
    print(f"Converting {npz_path} to {output_path}")

    return output_path
