import ast
import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple


class DependencyGraph:
    def __init__(self, file_paths: List[str]):
        """Initialize DependencyGraph with a list of file paths.

        Args:
            file_paths (List[str]): List of paths to analyze
        """
        self.file_paths = file_paths
        self.py_files = self._filter_python_files()
        self.graph = self._build_graph()

    def _filter_python_files(self) -> List[Tuple[str, str]]:
        """Filter out non-Python files and return list of (path, module) tuples."""
        py_files = []
        non_py_count = 0

        for path in self.file_paths:
            if not path.endswith(".py"):
                non_py_count += 1
                continue

            # Convert file path to module path
            module = os.path.splitext(path)[0].replace(os.sep, ".")
            if module.startswith("."):
                module = module[1:]
            py_files.append((path, module))

        if non_py_count > 0:
            print(f"Warning: {non_py_count} non-Python files excluded from analysis")

        return py_files

    def _parse_imports(self, file_path: str, module: str) -> Set[str]:
        """Parse Python file and extract its imports.

        Args:
            file_path (str): Path to Python file
            module (str): Module name corresponding to file path

        Returns:
            Set[str]: Set of imported module names
        """
        imports = set()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return imports

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

    def _build_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph using parallel processing.

        Returns:
            Dict[str, Set[str]]: Graph mapping modules to their dependencies
        """
        graph = defaultdict(set)
        project_modules = {module for _, module in self.py_files}

        def process_file(file_info: Tuple[str, str]) -> Tuple[str, Set[str]]:
            path, module = file_info
            imports = self._parse_imports(path, module)
            # Only keep imports that are part of the project
            internal_imports = {imp for imp in imports if imp in project_modules}
            return module, internal_imports

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_file, file_info): file_info
                for file_info in self.py_files
            }

            for future in as_completed(futures):
                module, imports = future.result()
                graph[module].update(imports)

        return graph

    def save_json(self, output_path: str):
        """Save dependency graph to JSON file.

        Args:
            output_path (str): Path to save JSON file
        """
        # Convert sets to lists for JSON serialization
        serializable = {module: list(deps) for module, deps in self.graph.items()}

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

        def dfs(node: str):
            if node in stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return

            visited.add(node)
            stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, []):
                dfs(neighbor)

            stack.remove(node)
            path.pop()

        for node in self.graph:
            if node not in visited:
                dfs(node)

        return cycles
