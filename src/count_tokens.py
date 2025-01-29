from typing import Dict, Optional

import tiktoken

from .file_getter import FileGetter


class TokenCounter:
    def __init__(self, repo_path: str = ".", model: str = "gpt-4o") -> None:
        """
        Initialize TokenCounter with repository path and model name.

        Args:
            repo_path: Path to the repository root
            model: Name of the model to use for tokenization (default: "gpt-4")
        """
        self.file_getter = FileGetter(repo_path)
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens_in_text(self, text: str) -> int:
        """
        Count the number of tokens in a given text.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens in the text
        """
        return len(self.tokenizer.encode(text))

    def count_tokens_in_file(self, file_path: str) -> Optional[int]:
        """
        Count tokens in a single file.

        Args:
            file_path: Path to the file relative to repo root

        Returns:
            Number of tokens in the file or None if file cannot be read
        """
        content = self.file_getter.read_file_text(file_path)
        if content is not None:
            return self.count_tokens_in_text(content)
        return None

    def count_all_files(self) -> Dict[str, Optional[int]]:
        """
        Count tokens in all files in the repository.

        Returns:
            Dictionary mapping file paths to their token counts
            Files that couldn't be read will have None as their value
        """
        token_counts: Dict[str, Optional[int]] = {}

        for file_path in self.file_getter.get_file_paths():
            token_counts[file_path] = self.count_tokens_in_file(file_path)

        return token_counts
