"""Benchmark dataset manager."""

import json
import zstandard as zstd
from pathlib import Path

from acados_template import (
    AcadosOcpQp,
    AcadosOcpQpSolver,
    AcadosOcpIterate,
    AcadosOcpQpOptions,
    AcadosCasadiOcpQpSolver,
)

import numpy as np

class BenchSetManager:
    """Manager for benchmark dataset collections."""

    def __init__(self, collection_path: str = "ocp_qp_dataset_collection"):
        """Initialize the manager.

        Args:
            collection_path: Path to the dataset collection folder.
        """
        self.collection_path = Path(collection_path)

    def add_problems_from_json_folder(
        self, source_path: Path, preferred_name: str
    ) -> list:
        """Add problems from a folder containing .json files to the collection.

        Each .json file should contain the data for one OCP-QP problem in a
        format that can be parsed by `AcadosOcpQp.from_json()`.

        The problems will be stored in a new subfolder of `collection_path`
        with the name `preferred_name` (or a modified version if that name
        already exists).

        Args:
            source_path: Path to folder containing JSON files.
            preferred_name: Preferred name for the problem set.

        Returns:
            List of added problem paths.
        """
        # Create a subset folder for json folder in collection_path
        new_name = preferred_name
        counter = 1
        self.dataset_path = self.collection_path / new_name

        # Find available name
        while self.dataset_path.exists():
            new_name = f"{preferred_name}_{counter}"
            self.dataset_path = self.collection_path / new_name
            counter += 1

        # Ask user once if name was changed
        if new_name != preferred_name:
            user_input = input(
                f"Folder '{preferred_name}' already exists. "
                f"Use '{new_name}' instead? (y/n): "
            )
            if user_input.lower() != "y":
                print("Operation cancelled.")
                return []

        self.dataset_path.mkdir()

        json_folder = Path(source_path).resolve()
        files = [f for f in json_folder.iterdir() if f.suffix == ".json"]
        added_problems = []

        for json_file in files:
            # Load problem
            try:
                qp = AcadosOcpQp.from_json(str(json_file))
            except Exception as e:
                print(
                    f"Error loading {json_file}:\n {e}\nSkipping this file."
                )
                continue
            # Generate problem set
            self._generate_problem_set(qp, new_name, json_file, added_problems)

        return added_problems

    def generate_meta_json(self, qp: AcadosOcpQp, name: str) -> dict:
        """Generate meta data dictionary for a QP problem.

        Args:
            qp: The OCP QP problem.
            name: Name for the problem.

        Returns:
            Dictionary containing meta data.
        """
        meta_json = {}
        meta_json["name"] = name
        meta_json["N"] = qp.N
        meta_json["has_slacks"] = qp.has_slacks()
        meta_json["has_masks"] = qp.has_masks()
        meta_json["has_idxs_rev_not_idxs"] = qp.has_idxs_rev_not_idxs()

        min_eigv = qp.qp_diagnostics()['min_eigv_global']
        if np.isclose(min_eigv, 0):
            meta_json["definiteness"] = "positive semidefinite"
        else:
            meta_json["definiteness"] = "indefinite" if min_eigv < 0 else "positive definite"

        return meta_json

    def generate_reference_solution(
        self, qp: AcadosOcpQp, meta_dict: dict
    ) -> AcadosOcpIterate:
        """Generate a reference solution for a QP problem.

        Args:
            qp: The OCP QP problem.

        Returns:
            Reference solution iterate, or None if solve failed.
        """
        qp_solver = AcadosCasadiOcpQpSolver(qp, solver='ipopt', solver_opts={"print_time": False, "ipopt": {"print_level": 0}})
        status = qp_solver.solve()
        if status == 0:
            print("Reference solution found.")
            ref_sol: AcadosOcpIterate = qp_solver.get_iterate()
            return ref_sol
        else:
            print("No solution found.")
            return None

    def _generate_problem_set(self, qp, new_name, json_file, added_problems):
        cctx = zstd.ZstdCompressor()
        # Generate meta data and reference solution
        meta_dict = self.generate_meta_json(
            qp, name=f"{new_name}_{json_file.name}"
        )
        ref_sol = self.generate_reference_solution(qp, meta_dict)
        meta_dict["has_reference_solution"] = ref_sol is not None

        # Create new folder
        new_folder_path = self.dataset_path / json_file.stem
        new_folder_path.mkdir()

        original_data_bytes = json_file.read_bytes()
        compressed_data = cctx.compress(original_data_bytes)
        (new_folder_path / f"{json_file.name}.zst").write_bytes(compressed_data)

        # Save meta json
        (new_folder_path / f"{json_file.stem}_meta.json").write_text(
            json.dumps(meta_dict, indent=4), encoding='utf-8'
        )

        if ref_sol is not None:
            # Save reference solution
            ref_sol_json_str = ref_sol.to_json()
            compressed_ref_sol = cctx.compress(ref_sol_json_str.encode('utf-8'))
            (new_folder_path / f"{json_file.stem}_ref_sol.json.zst").write_bytes(compressed_ref_sol)
        print(f"Added and compressed problem from {json_file} to {new_folder_path}")
        added_problems.append(str(new_folder_path))

    def sanitize_problem_set(self):
        """Run through all problems, check for sanity, generate missing meta data."""
        raise NotImplementedError()
