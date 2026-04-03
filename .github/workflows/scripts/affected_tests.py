import subprocess
import os
import sys
import logging


_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main() -> None:
    """Function to identify and run affected tests based on changed Python files in a PR."""
    changed_py_files = get_changed_py_files()
    if not changed_py_files:
        _LOGGER.info("No Python files changed. Skipping impacted test analysis.")
        return
    dependency_map = build_dependency_graph()
    tests_to_run = get_affected_tests(changed_py_files, dependency_map)
    if not tests_to_run:
        _LOGGER.warning("No affected tests found. Skipping test execution.")
        return

    # Write the affected tests into the Github Actions output variable for use in subsequent steps
    _LOGGER.info(f"Affected tests identified: {tests_to_run}")
    os.environ["AFFECTED_TESTS"] = " ".join(tests_to_run)
    _LOGGER.debug(f"Setting AFFECTED_TESTS environment variable to: {os.environ['AFFECTED_TESTS']}")


def get_changed_py_files() -> set[str]:
    """Find all changed Python files in the PR."""
    base_ref = os.environ.get("GITHUB_BASE_REF", "main")

    try:
        # Comparing the PR branch against the base branch origin
        changed_files_raw = subprocess.check_output(
            ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"], text=True
        )
    except subprocess.CalledProcessError:
        # Fallback for shallow clones or local execution
        changed_files_raw = subprocess.check_output(["git", "diff", "--name-only", "HEAD^"], text=True)
    return {f for f in changed_files_raw.splitlines() if f.endswith(".py")}


def build_dependency_graph() -> dict[str, set[str]]:
    """Build a dependency graph from ruff's output.

    Returns:
        A dictionary mapping each Python file to a set of files it imports.
    """
    try:
        graph_raw = subprocess.check_output(["/usr/bin/uv", "run", "ruff", "analyze", "graph"], text=True)
    except subprocess.CalledProcessError as e:
        _LOGGER.exception(f"Error executing 'ruff analyze graph': {e}")
        sys.exit(1)

    dependency_map = {}
    current_file = None
    for line in graph_raw.splitlines():
        if line and not line.startswith("  "):
            current_file = line.strip()
            dependency_map[current_file] = set()
        elif current_file and "imports" in line:
            imported = line.split("imports")[-1].strip()
            dependency_map[current_file].add(imported)
    return dependency_map


def get_affected_tests(changed_files: set[str], dependency_map: dict[str, set[str]]) -> set[str]:
    """Determine which tests are affected based on changed files and the dependency graph.

    Args:
        changed_files: A set of changed Python files.
        dependency_map: A mapping of Python files to their imports.

    Returns:
        A set of affected test files.
    """

    def _is_affected(file_path: str, visited: set[str] | None = None) -> bool:
        """Recursively checks if a file is affected by changes."""
        if visited is None:
            visited = set()
        if file_path in changed_files:
            return True
        if file_path in visited:
            return False
        visited.add(file_path)

        return any(_is_affected(imp, visited) for imp in dependency_map.get(file_path, []))

    return {f for f in dependency_map if f.startswith("tests/") and f.endswith(".py") and _is_affected(f)}


if __name__ == "__main__":
    main()
