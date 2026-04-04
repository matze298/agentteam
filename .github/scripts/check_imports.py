import ast
import logging
import sys
import tomllib
import typer
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


def get_workspace_members(root_path: Path) -> list[Path]:
    with open(root_path / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    members = data.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", [])
    return [root_path / member for member in members]


def get_declared_dependencies(project_path: Path) -> set[str]:
    pyproject_file = project_path / "pyproject.toml"
    if not pyproject_file.exists():
        return set()

    with open(pyproject_file, "rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    # Basic parsing of PEP 508 strings (extracting the package name)
    declared = {
        dep.split(">")[0].split("=")[0].split("<")[0].split("[")[0].strip().lower().replace("-", "_") for dep in deps
    }

    # Add optional dependencies if needed
    optional = data.get("project", {}).get("optional-dependencies", {})
    for group in optional.values():
        for dep in group:
            declared.add(dep.split(">")[0].split("=")[0].strip().lower().replace("-", "_"))

    return declared


def get_imports_from_file(file_path: Path) -> set[str]:
    imports = set()
    try:
        with Path(file_path).open("r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    imports.add(node.module.split(".")[0])
    except Exception as e:
        _LOGGER.exception(f"Error parsing {file_path}: {e}")
    return imports


def main(*, verbose: bool = True):
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s", stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    root_path = Path.cwd()
    members = get_workspace_members(root_path)
    if not members:
        members = [root_path]  # Fallback to root if not a workspace

    # Standard library modules (approximate list for Python 3.10+)
    stdlib = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else set()

    exit_code = 0

    for member in members:
        declared_deps: set[str] = get_declared_dependencies(member)

        # allowed_imports is what we use to check for missing imports (includes workspace members)
        allowed_imports = declared_deps.copy()
        allowed_imports.add(member.name.lower().replace("-", "_"))
        for m in members:
            allowed_imports.add(m.name.lower().replace("-", "_"))

        used_imports = set()
        # Scan src or member directory
        search_dir = member / "src" if (member / "src").is_dir() else member
        for py_file in search_dir.rglob("*.py"):
            if ".venv" in py_file.parts or "tests" in py_file.parts:
                continue
            used_imports.update(get_imports_from_file(py_file))

        # Filter out stdlib
        external_used = {imp.lower().replace("-", "_") for imp in used_imports if imp not in stdlib}

        # Find missing: things imported but not declared
        missing = external_used - allowed_imports

        # Find unused: things declared but not imported
        # We exclude common CLI tools that aren't usually imported in code
        cli_only_tools = {"pytest", "ruff", "prek", "ty", "mypy", "black", "isort", "pytest_xdist"}
        unused = declared_deps - external_used - cli_only_tools

        # Filter out local directory modules (rough check)
        missing = {m for m in missing if not (member / m).is_dir() and not (member / "src" / m).is_dir()}

        _LOGGER.debug(f"Project '{member.name}' has declared dependencies: {declared_deps}")
        _LOGGER.debug(f"Project '{member.name}' has used imports: {external_used}")

        if missing:
            _LOGGER.error(
                f"❌ Project '{member.name}' is missing dependencies: {', '.join(sorted(missing))}. Please add them to pyproject.toml."
            )
            exit_code = 1
        if unused:
            _LOGGER.error(
                f"❌ Project '{member.name}' has unused dependencies: {', '.join(sorted(unused))}. Please remove them from pyproject.toml."
            )
            exit_code = 1
        else:
            _LOGGER.info(f"✅ Project '{member.name}' dependencies look correct.")

    sys.exit(exit_code)


if __name__ == "__main__":
    typer.run(main)
