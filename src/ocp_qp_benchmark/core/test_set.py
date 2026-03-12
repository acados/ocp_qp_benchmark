"""Test set management."""

import os
from typing import Any, Callable, Dict

from ocp_qp_benchmark.utils.io import load_meta_data


class TestSet:
    """Represents a collection of QP problems for benchmarking."""

    @property
    def description(self) -> str:
        return self.__description

    @description.setter
    def description(self, value: str) -> None:
        self.__description = value

    @property
    def title(self) -> str:
        return self.__description

    def __init__(self, qp_folder_paths: list[str] = None, verbose: bool = True):
        """
        Initialize test set.
        Args:
            qp_folder_paths: List of paths to folders containing QP problems.(e.g., ["ocp_qp_dataset_collection/random_qp/prob_0", ...])
            if None, all problems from the dataset collection will be used.

            verbose: Whether to print information about found folders.
        """
        if qp_folder_paths is None:
            raise ValueError("No QP folder paths provided. Please provide a list of paths to QP problem folders.")

        self.qp_folder_paths = qp_folder_paths
        subfolders = [os.path.basename(path) for path in qp_folder_paths]
        if verbose:
            print("Designated QP problems:")
            for folder in subfolders:
                print(f"  - {folder}")
        self.__description = ""

    def __iter__(self):
        """Iterator over all problems in the test set."""
        for qp_folder_path in self.qp_folder_paths:
            qp_folder_name = os.path.basename(qp_folder_path)
            if os.path.isdir(qp_folder_path):
                path_dict = {
                    "qp_data_path": os.path.join(
                        qp_folder_path, f"{qp_folder_name}.json"
                    ),
                    "meta_data_path": os.path.join(
                        qp_folder_path, f"{qp_folder_name}_meta.json"
                    ),
                    "ref_sol_path": os.path.join(
                        qp_folder_path, f"{qp_folder_name}_ref_sol.json"
                    ),
                }
                yield path_dict

    def count_problems(self) -> int:
        """Count the number of problems in the test set."""
        return len(self.qp_folder_paths)

    def filter_problems(self, opts : dict = None, verbose: bool = True) -> None:
        """
        Filter problems based on options.
        Args:
            opts: Dictionary of options to filter by (e.g., {"has_slacks": True})
        """
        if opts is None:
            return self.qp_folder_paths
        target_conditions = {k: v for opt in opts for k, v in opt.items()}
        filtered_paths = []
        for path in self.qp_folder_paths:
            if not os.path.isdir(path):
                continue
            meta_data = load_meta_data(path)
            is_fully_matched = all(
                meta_data.get(k) == v for k, v in target_conditions.items()
            )
            if is_fully_matched:
                filtered_paths.append(path)
        self.qp_folder_paths = filtered_paths
        if verbose:
            print("Filtered QP problems:")
            for folder in filtered_paths:
                print(f"  - {folder}")