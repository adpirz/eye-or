from dataclasses import dataclass, field
from typing import Dict, List, Optional

from file_info import FileInfo


@dataclass
class Graph:
    """
    A dataclass representing a dependency graph of Python files.
    Contains an entry point file and tracks source nodes (files with no dependencies).
    """

    files: Dict[str, FileInfo]
    entry_point: Optional[FileInfo] = None
    source_nodes: List[FileInfo] = field(default_factory=list)

    def __post_init__(self):
        """
        Validates the graph structure and computes source nodes.

        Raises:
            ValueError: If entry_point is None and no 'main.py' is found
        """
        # If no entry point specified, look for main.py
        if self.entry_point is None:
            main_candidates = [
                f for f in self.files.values() if f.relative_path.name == "main.py"
            ]
            if not main_candidates:
                raise ValueError("No entry point specified and no main.py found")
            self.entry_point = main_candidates[0]

        # Compute source nodes (files with no dependencies)
        self.source_nodes = [
            file_info for file_info in self.files.values() if not file_info.dependencies
        ]
