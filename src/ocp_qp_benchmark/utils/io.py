"""I/O utility functions."""

import json
import os
import zstandard as zstd

def load_data(json_path: str) -> dict:
    """
    Load meta data from the meta.json file for a given problem folder.

    Args:
        qp_folder_path: Path to the QP problem folder.

    Returns:
        Dictionary containing the meta data.
    """
    with open(json_path, "r") as f:
        return json.load(f)

def decompress(zstd_path) -> None:
    """
    Decompress a zstd compressed json file into json data.

    Args:
        zstd_path: Path to the zstd compressed json file.
    """
    dctx = zstd.ZstdDecompressor()
    with open(zstd_path, 'rb') as f:
        decompressed_data = dctx.decompress(f.read())
        json_data = json.loads(decompressed_data.decode('utf-8'))
    return json_data