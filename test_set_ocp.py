import os
import json
from typing import Dict, Any, Callable

from utils import load_meta_data

class TestSet():

    @property
    def description(self) -> str:
        return self.__description

    @description.setter
    def description(self, value: str) -> None:
        self.__description = value

    @property
    def title(self) -> str:
        return self.__description

    def __init__(self,
                 qp_folder_paths: list[str]):
        """Initialize test set."""

        self.qp_folder_paths = qp_folder_paths
        self.__description = ""

    def __iter__(self):
        """Iterator over all problems in the test set."""
        for qp_folder_path in self.qp_folder_paths:
            qp_folder_name = os.path.basename(qp_folder_path)
            if os.path.isdir(qp_folder_path):
                path_dict = {
                    'qp_data_path': os.path.join(qp_folder_path, f"{qp_folder_name}.json"),
                    'meta_data_path': os.path.join(qp_folder_path, f"{qp_folder_name}_meta.json"),
                    'ref_sol_path': os.path.join(qp_folder_path, f"{qp_folder_name}_ref_sol.json"),
                }
                yield path_dict

    def count_problems(self) -> int:
        """Count the number of problems in the test set."""
        return len(self.qp_folder_paths)

    def filter_by_meta(self, filter_func: Callable[[Dict[str, Any]], bool]):
        """
        Filter problems based on meta data using a custom filter function.

        Args:
            filter_func: A function that takes meta data dict and returns True if problem should be included

        Returns:
            A new TestSet instance with filtered problems
        """
        filtered_paths = []

        for qp_folder_path in self.qp_folder_paths:
            if os.path.isdir(qp_folder_path):
                meta_data = load_meta_data(qp_folder_path)
                if filter_func(meta_data):
                    filtered_paths.append(qp_folder_path)

        return TestSet(filtered_paths)

    def filter_has_slacks(self, has_slacks: bool = True):
        """
        Filter problems based on whether they have slacks.
        """
        return self.filter_by_meta(lambda meta: meta.get('has_slacks', False) == has_slacks)

    def filter_has_masks(self, has_masks: bool = True):
        return self.filter_by_meta(lambda meta: meta.get('has_masks', False) == has_masks)

    def filter_has_idxs_rev_not_idxs(self, has_idxs_rev_not_idxs: bool = True):
        return self.filter_by_meta(lambda meta: meta.get('has_idxs_rev_not_idxs', False) == has_idxs_rev_not_idxs)
