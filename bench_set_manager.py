import shutil
import json
from pathlib import Path
from acados_template import AcadosOcpQp, AcadosOcpQpSolver, AcadosOcpIterate, AcadosOcpQpOptions


class BenchSetManager():
    def __init__(self):
        self.collection_path = Path('ocp_qp_dataset_collection')

    def add_problems_from_json_folder(self, source_path: Path, preferred_name: str) -> list:
        """
        Add problems from a folder `source_path` containing .json files to the collection.
        Each .json file should contain the data for one OCP-QP problem in a format that can be parsed by `AcadosOcpQp.from_json()`.
        The problems will be stored in a new subfolder of `collection_path` with the name `preferred_name` (or a modified version if that name already exists).
        """
        # create a subset folder for json folder in collection_path with preferred_name
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
            user_input = input(f"Folder '{preferred_name}' already exists. Use '{new_name}' instead? (y/n): ")
            if user_input.lower() != 'y':
                print("Operation cancelled.")
                return []

        self.dataset_path.mkdir()

        json_folder = Path(source_path).resolve()
        files = [f for f in json_folder.iterdir() if f.suffix == '.json']
        for json_file in files:

            # load problem
            try:
                qp = AcadosOcpQp.from_json(str(json_file))
            except Exception as e:
                print(f"Error loading {json_file}:\n {e}\nSkipping this file.")
                continue

            # generate meta data and reference solution
            meta_dict = self.generate_meta_json(qp, name=f'{new_name}_{json_file.name}')
            ref_sol = self.generate_reference_solution(qp)

            # create new folder
            new_folder_path = self.dataset_path / json_file.stem
            new_folder_path.mkdir()

            # copy json file
            shutil.copy2(json_file, new_folder_path / json_file.name)

            # save meta json
            (new_folder_path / f'{json_file.stem}_meta.json').write_text(json.dumps(meta_dict, indent=4))

            if ref_sol is not None:
                # save reference solution by writing ref_sol.to_json()
                (new_folder_path / f'{json_file.stem}_ref_sol.json').write_text(ref_sol.to_json())
            print(f"Added problem from {json_file} to {new_folder_path}")

    def generate_meta_json(self, qp: AcadosOcpQp, name: str) -> dict:
        meta_json = {}
        meta_json['name'] = name
        meta_json['N'] = qp.N
        meta_json['has_slacks'] = qp.has_slacks()
        meta_json['has_masks'] = qp.has_masks()
        meta_json['has_idxs_rev_not_idxs'] = qp.has_idxs_rev_not_idxs()
        return meta_json

    def generate_reference_solution(self, qp: AcadosOcpQp) -> dict:
        opts = AcadosOcpQpOptions()
        opts.qp_solver = 'PARTIAL_CONDENSING_HPIPM'
        opts.print_level = 0
        solver = AcadosOcpQpSolver(qp, opts)
        status = solver.solve()
        if status == 0:
            print("Reference solution found.")
            ref_sol: AcadosOcpIterate = solver.get_iterate()
        else:
            print("Warning: Reference solution not found, status:", status)
            ref_sol: AcadosOcpIterate = None
        return ref_sol

    def sanitize_problem_set(self):
        # run through all problems
        # check for sanity
        # generate meta data if missing
        raise NotImplementedError()
