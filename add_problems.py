from pathlib import Path
from bench_set_manager import BenchSetManager
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add problems to benchmark set')
    parser.add_argument('folder_path', help='Path to folder containing JSON files')
    parser.add_argument('--name', '-n', default='qps',
                       help='Name of the problem set to be added (default: qps)')

    args = parser.parse_args()

    manager = BenchSetManager()
    manager.add_problems_from_json_folder(Path(args.folder_path), args.name)
