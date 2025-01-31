import argparse
from pathlib import Path

from dependency_graph import DependencyGraph
from file_getter import FileGetter, parse_pattern_list


def get_common_module_prefix(modules):
    """Find the common prefix of module paths using dot notation."""
    if not modules:
        return ""

    # Split all modules into their components
    split_modules = [mod.split(".") for mod in modules]

    # Find the common prefix components
    common = []
    for parts in zip(*split_modules):
        if len(set(parts)) != 1:
            break
        common.append(parts[0])

    return ".".join(common)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a dependency graph for Python files in a repository."
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the repository (defaults to current directory)",
    )
    parser.add_argument(
        "--include",
        type=parse_pattern_list,
        help=(
            "Comma-separated glob patterns to include. Use quotes for patterns "
            'containing commas. Example: "*.py,src/**/*.py"'
        ),
    )
    parser.add_argument(
        "--exclude",
        type=parse_pattern_list,
        help=(
            "Comma-separated glob patterns to exclude. Use quotes for patterns "
            'containing commas. Example: "test_*.py,**/*.tmp"'
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Path to save the dependency graph as JSON",
    )
    parser.add_argument(
        "--check-cycles",
        action="store_true",
        help="Check and report any dependency cycles",
    )

    args = parser.parse_args()

    # Get all files from the repository
    file_getter = FileGetter(
        repo_path=args.repo_path,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
    )

    # Build dependency graph
    files = file_getter.get_file_paths()
    dep_graph = DependencyGraph(files, args.repo_path)

    # Compute common prefix to trim from module paths
    common_prefix = get_common_module_prefix(list(dep_graph.graph.keys()))

    # Save to JSON if output path specified
    if args.output:
        output_path = Path(args.output)
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dep_graph.save_json(str(output_path))
    else:
        # Print the graph to stdout if no output file specified
        for module, deps in dep_graph.graph.items():
            trimmed_module = (
                module[len(common_prefix) + 1 :]
                if common_prefix and module.startswith(common_prefix)
                else module
            )
            trimmed_deps = [
                dep[len(common_prefix) + 1 :]
                if common_prefix and dep.startswith(common_prefix)
                else dep
                for dep in deps
            ]
            print(f"{trimmed_module} -> {list(trimmed_deps)}")

    # Check for cycles if requested
    if args.check_cycles:
        cycles = dep_graph.detect_cycles()
        if cycles:
            print("\nWarning: Dependency cycles detected:")
            for cycle in cycles:
                trimmed_cycle = [
                    mod[len(common_prefix) + 1 :]
                    if common_prefix and mod.startswith(common_prefix)
                    else mod
                    for mod in cycle
                ]
                print(" -> ".join(trimmed_cycle))
        else:
            print("\nNo dependency cycles detected.")


if __name__ == "__main__":
    main()
