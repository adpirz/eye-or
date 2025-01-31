from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Union


@dataclass
class FileInfo:
    """
    A dataclass representing a Python file with its absolute path and root path information.
    The relative path is derived from these two paths.
    """

    absolute_path: Union[str, Path]
    root_path: Union[str, Path]
    dependencies: Set["FileInfo"] = field(default_factory=set)

    def __post_init__(self):
        """
        Convert paths to Path objects and validate that root_path is a parent of absolute_path.

        Raises:
            ValueError: If root_path is not a parent directory of absolute_path
        """
        if isinstance(self.absolute_path, str):
            self.absolute_path = Path(self.absolute_path)
        if isinstance(self.root_path, str):
            self.root_path = Path(self.root_path)

        # Resolve both paths to their absolute form
        self.absolute_path = self.absolute_path.resolve()
        self.root_path = self.root_path.resolve()

        # Validate that root_path is a parent of absolute_path
        try:
            self.absolute_path.relative_to(self.root_path)
        except ValueError:
            raise ValueError(
                f"Root path '{self.root_path}' must be a parent directory of absolute path '{self.absolute_path}'"
            )

    @property
    def relative_path(self) -> Path:
        """Returns the relative path from the root path."""
        return self.absolute_path.relative_to(self.root_path)

    def __str__(self) -> str:
        """String representation showing both absolute and relative paths."""
        return f"{self.absolute_path} (relative: {self.relative_path})"

    def __eq__(self, other):
        if not isinstance(other, FileInfo):
            return False
        return self.absolute_path == other.absolute_path

    def __hash__(self):
        return hash(self.absolute_path)
