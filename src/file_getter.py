import argparse
import fnmatch
import os
from functools import lru_cache
from pathlib import Path
from typing import Iterator, List, Optional, Set, Union

from common_ignores import COMMON_IGNORE_PATTERNS


class FileGetter:
    def __init__(
        self,
        repo_path: Union[str, Path] = ".",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> None:
        """
        Initializes the FileGetter.

        Args:
            repo_path: Path to the repository root.
            include_patterns: List of glob patterns to include.
            exclude_patterns: List of glob patterns to exclude.

        Raises:
            ValueError: If the repository path doesn't exist or isn't a directory.
        """
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {repo_path}")

        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.ignored_files = self._get_gitignore_patterns()
        self.file_paths = self._retrieve_file_paths()

    # Using LRU cache here for performance optimization since:
    # 1. The .gitignore patterns rarely change during the lifetime of an instance
    # 2. Reading and parsing .gitignore is an I/O operation we want to minimize
    # 3. The patterns are used frequently during file traversal
    # maxsize=1 is sufficient as the patterns only depend on the repo_path,
    # which is set at initialization
    @lru_cache(maxsize=1)
    def _get_gitignore_patterns(self) -> Set[str]:
        """
        Retrieves patterns from .gitignore and adds common ignore patterns.
        Uses lru_cache for performance optimization.

        Returns:
            Set of ignore patterns.
        """
        patterns: Set[str] = set()
        gitignore_path = self.repo_path / ".gitignore"

        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r") as f:
                    # Read patterns directly from .gitignore file
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.add(line)
            except Exception:
                # If there's any error reading .gitignore, just use common patterns
                pass

        patterns.update(COMMON_IGNORE_PATTERNS)
        return patterns

    def _is_ignored(self, file_path: Path, is_dir: bool = False) -> bool:
        """
        Determines if a file or directory should be ignored.

        Args:
            file_path: Path to the file or directory.
            is_dir: True if the path is a directory.

        Returns:
            True if ignored, False otherwise.
        """
        try:
            relative_path = file_path.relative_to(self.repo_path)
        except ValueError:
            return True  # Path is outside repo directory

        # Check exclude patterns
        if any(
            fnmatch.fnmatch(str(relative_path), pattern)
            for pattern in self.exclude_patterns
        ):
            return True

        if not is_dir:
            # Check include patterns only for files
            if self.include_patterns and not any(
                fnmatch.fnmatch(str(relative_path), pat)
                for pat in self.include_patterns
            ):
                return True

        # Check .gitignore and common ignores
        return any(
            fnmatch.fnmatch(str(relative_path), pat) for pat in self.ignored_files
        )

    def _retrieve_file_paths(self) -> List[Path]:
        """
        Retrieves the list of file paths in the repository based on the patterns.

        Returns:
            List of Path objects.
        """
        file_paths: List[Path] = []

        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [
                d for d in dirs if not self._is_ignored(root_path / d, is_dir=True)
            ]

            for file in files:
                file_path = root_path / file
                if not self._is_ignored(file_path, is_dir=False):
                    try:
                        file_paths.append(file_path.relative_to(self.repo_path))
                    except ValueError:
                        continue  # Skip files outside repo directory

        return file_paths

    def get_file_paths(self, relative: bool = False) -> List[str]:
        """
        Returns the list of file paths as strings.

        Args:
            relative: If True, returns paths relative to repo_path. If False, returns absolute paths.

        Returns:
            List of file paths as strings.
        """
        if relative:
            return [str(path) for path in self.file_paths]
        return [str(self.repo_path / path) for path in self.file_paths]

    def read_file_text(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Reads the content of a file as text.

        Args:
            file_path: Path to the file.

        Returns:
            File content as string or None if file cannot be read.

        Raises:
            UnicodeDecodeError: If the file cannot be decoded as UTF-8.
            PermissionError: If there are insufficient permissions to read the file.
        """
        path = self.repo_path / file_path
        try:
            if path.exists() and path.is_file():
                return path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError) as e:
            raise e
        except Exception:
            return None
        return None

    def read_file_stream(
        self, file_path: Union[str, Path]
    ) -> Optional[Iterator[bytes]]:
        """
        Reads the content of a file as a binary stream.

        Args:
            file_path: Path to the file.

        Returns:
            An iterator of bytes or None if file cannot be read.

        Raises:
            PermissionError: If there are insufficient permissions to read the file.
        """
        path = self.repo_path / file_path
        try:
            if path.exists() and path.is_file():
                return iter([path.read_bytes()])
        except PermissionError as e:
            raise e
        except Exception:
            return None
        return None


def parse_pattern_list(arg: str) -> List[str]:
    """
    Parse a comma-separated string of glob patterns, preserving any commas that are part of the patterns.
    Patterns can be quoted if they contain commas.

    Args:
        arg: Comma-separated string of patterns

    Returns:
        List of patterns
    """
    patterns = []
    current = []
    in_quotes = False

    for char in arg:
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            if current:
                patterns.append("".join(current).strip().strip('"'))
                current = []
        else:
            current.append(char)

    if current:
        patterns.append("".join(current).strip().strip('"'))

    return patterns


def main():
    parser = argparse.ArgumentParser(description="List files in a repository.")
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the repository (defaults to current directory)",
    )
    parser.add_argument(
        "--include",
        type=parse_pattern_list,
        help='Comma-separated glob patterns to include. Use quotes for patterns containing commas. Example: "*.py,*.js,src/**/*.{cpp,h}"',
    )
    parser.add_argument(
        "--exclude",
        type=parse_pattern_list,
        help='Comma-separated glob patterns to exclude. Use quotes for patterns containing commas. Example: "test_*.py,**/*.tmp"',
    )

    args = parser.parse_args()
    file_getter = FileGetter(
        repo_path=args.repo_path,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
    )
    print(file_getter.get_file_paths())


if __name__ == "__main__":
    main()
