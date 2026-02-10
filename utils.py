import json
import os


def load_meta_data(qp_folder_path: str) -> dict:
    """Load meta data from the meta.json file for a given problem folder."""
    qp_folder_name = os.path.basename(qp_folder_path)
    meta_data_path = os.path.join(qp_folder_path, f"{qp_folder_name}_meta.json")
    with open(meta_data_path, 'r') as f:
        return json.load(f)
