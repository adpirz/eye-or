import ast
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from file_info import FileInfo
from graph import Graph


class DependencyGraph:
    def __init__(self, file_paths: List[str], root_path: Union[str, Path]):
        """Initialize DependencyGraph with a list of file paths.

        Args:
            file_paths (List[str]): List of absolute paths to analyze
            root_path (Union[str, Path], optional): Root path for relative path calculations.
                                                  If not provided, uses the common parent of all files.
        """
        if root_path is None:
            raise ValueError("Could not determine common parent directory for files")

        self.root_path = Path(root_path).resolve()
        self.files: Dict[str, FileInfo] = {}
        self._initialize_files(file_paths)
        self.graph = self._build_graph()

    def _initialize_files(self, file_paths: List[str]):
        """Create FileInfo instances for all Python files."""
        for path in file_paths:
            if not str(path).endswith(".py"):
                continue
            file_info = FileInfo(path, self.root_path)
            # Use relative path as key for consistent lookup
            self.files[str(file_info.relative_path)] = file_info

    def _parse_imports(self, file_info: FileInfo) -> Set[str]:
        """Parse Python file and extract its imports.

        Args:
            file_info (FileInfo): FileInfo object for the Python file

        Returns:
            Set[str]: Set of imported module paths (relative to root)
        """
        imports = set()
        try:
            with open(file_info.absolute_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_info.absolute_path))
        except Exception as e:
            print(f"Error parsing {file_info.absolute_path}: {e}")
            return imports

        module = str(file_info.relative_path.with_suffix("")).replace(os.sep, ".")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.level == 0:
                        imports.add(node.module)
                    else:
                        # Handle relative imports
                        parent_modules = module.split(".")[: (-node.level)]
                        if parent_modules:
                            resolved = ".".join(
                                parent_modules + [node.module.split(".")[0]]
                            )
                            imports.add(resolved)

        return imports

    def _build_graph(self) -> Graph:
        """Build dependency graph using parallel processing.

        Returns:
            Graph: A Graph instance containing all files and their dependencies
        """

        def process_file(file_info: FileInfo) -> Tuple[FileInfo, Set[str]]:
            imports = self._parse_imports(file_info)
            return file_info, imports

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_file, file_info): file_info
                for file_info in self.files.values()
            }

            for future in as_completed(futures):
                file_info, imports = future.result()
                # Convert module imports to FileInfo dependencies
                for imp in imports:
                    # Convert module path to file path
                    file_path = imp.replace(".", os.sep) + ".py"
                    if file_path in self.files:
                        file_info.dependencies.add(self.files[file_path])

        return Graph(files=self.files)

    def save_json(self, output_path: str):
        """Save dependency graph to JSON file.

        Args:
            output_path (str): Path to save JSON file
        """
        # Convert to serializable format
        serializable = {
            str(file_info.relative_path): [
                str(dep.relative_path) for dep in file_info.dependencies
            ]
            for file_info in self.files.values()
        }

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=4)
            print(f"Dependency graph saved to {output_path}")
        except Exception as e:
            print(f"Error saving to {output_path}: {e}")

    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the dependency graph using DFS.

        Returns:
            List[List[str]]: List of cycles found
        """
        visited = set()
        stack = set()
        cycles = []
        path = []

        def dfs(file_info: FileInfo):
            if file_info in stack:
                cycle_start = path.index(file_info)
                cycles.append(
                    [str(f.relative_path) for f in path[cycle_start:]]
                    + [str(file_info.relative_path)]
                )
                return
            if file_info in visited:
                return

            visited.add(file_info)
            stack.add(file_info)
            path.append(file_info)

            for dep in file_info.dependencies:
                dfs(dep)

            stack.remove(file_info)
            path.pop()

        for file_info in self.files.values():
            if file_info not in visited:
                dfs(file_info)

        return cycles
