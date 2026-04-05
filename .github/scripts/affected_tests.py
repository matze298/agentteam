#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#     "typer",
# ]
# ///

"""Identify unit tests to be executed based on changed Python files."""

import logging
import os
import subprocess
import sys

import typer

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
    # In GitHub Actions, GITHUB_EVENT_NAME is 'pull_request' for PRs.
    # github.event.pull_request.base.sha is the most reliable base commit for a PR.
    # We can try to get this from an environment variable if passed from the workflow.
    github_base_sha = os.environ.get("GITHUB_BASE_SHA")

    try:
        if github_base_sha:
            _LOGGER.info(f"Comparing with GITHUB_BASE_SHA: {github_base_sha}")
            # Compare current HEAD with the base SHA of the PR
            changed_files_raw = subprocess.check_output(
                ["git", "diff", "--name-only", github_base_sha, "HEAD"], text=True
            )
        else:
            base_ref = os.environ.get("GITHUB_BASE_REF", "main")
            _LOGGER.info(f"GITHUB_BASE_SHA not available. Attempting to find merge-base with origin/{base_ref}.")
            # Fallback: find the merge base between the base branch and HEAD
            # This requires 'origin/{base_ref}' to be a valid ref, which means it must be fetched.
            merge_base_cmd = ["git", "merge-base", f"origin/{base_ref}", "HEAD"]
            merge_base = subprocess.check_output(merge_base_cmd, text=True).strip()
            _LOGGER.info(f"Merge base identified as: {merge_base}")
            changed_files_raw = subprocess.check_output(["git", "diff", "--name-only", merge_base, "HEAD"], text=True)
    except subprocess.CalledProcessError as e:
        _LOGGER.warning(
            f"Failed to get changes using GITHUB_BASE_SHA or merge-base (error: {e}). "
            "Falling back to 'git diff HEAD^' (may not be accurate for PRs)."
        )
        # Fallback for shallow clones, local execution, or if base branch is not fetched
        changed_files_raw = subprocess.check_output(["git", "diff", "--name-only", "HEAD^"], text=True)
    except FileNotFoundError:
        _LOGGER.exception("Git command not found. Ensure Git is installed and in PATH.")
        sys.exit(1)
    return {f for f in changed_files_raw.splitlines() if f.endswith(".py")}


def build_dependency_graph() -> dict[str, set[str]]:
    """Build a dependency graph from ruff's output.

    Returns:
        A dictionary mapping each Python file to a set of files it imports.
    """
    try:
        graph_raw = subprocess.check_output(["uv", "run", "ruff", "analyze", "graph"], text=True)
    except subprocess.CalledProcessError:
        _LOGGER.exception("Error executing 'ruff analyze graph'.")
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
    typer.run(main)
