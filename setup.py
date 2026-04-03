#!/usr/bin/env -S uv run --script

"""Setup the DevEnvironment via Typer."""
# /// script
# dependencies = [
# "typer",
# ]
# ///

import subprocess
from typing import Final
import typer
from pathlib import Path

VENV_DIR: Final = ".venv"


def setup(*, yes_please: bool = False, recreate_venv: bool = False) -> None:
    """Setup the DevEnvironment."""
    # Check if uv is installed
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        typer.secho("✅ UV is already installed.", fg=typer.colors.GREEN)
    except (subprocess.CalledProcessError, FileNotFoundError):
        msg = "❌ UV is not installed. Shall I install it for you? (y/n)"
        if typer.confirm(msg) or yes_please:
            _install_uv()

    # Create a virtual environment using UV
    if not Path(VENV_DIR).is_dir():
        typer.secho(f"⏳ Creating virtual environment at {VENV_DIR}...", fg=typer.colors.YELLOW)
        subprocess.check_call(["uv", "venv", VENV_DIR])
        typer.secho("✅ Virtual environment created successfully.", fg=typer.colors.GREEN)
    else:
        typer.secho("✅ Virtual environment already exists.", fg=typer.colors.GREEN)
        if recreate_venv:
            typer.secho("⏳ Recreating virtual environment...", fg=typer.colors.YELLOW)
            subprocess.check_call(["uv", "venv", VENV_DIR, "--clear"])
            typer.secho("✅ Virtual environment recreated successfully.", fg=typer.colors.GREEN)

    # Install dependencies
    if not Path("uv.lock").is_file():
        msg = "❌ No uv.lock file found. Shall I create one for you? (y/n)"
        if typer.confirm(msg) or yes_please:
            typer.secho("⏳ Creating uv.lock...", fg=typer.colors.YELLOW)
            subprocess.check_call(["uv", "lock"])
            typer.secho("✅ uv.lock created successfully.", fg=typer.colors.GREEN)
    else:
        typer.secho("✅ uv.lock already exists.", fg=typer.colors.GREEN)

    # Sync dependencies
    subprocess.check_call(["uv", "sync", "--all-extras"])
    typer.secho("✅ Dependencies installed successfully.", fg=typer.colors.GREEN)

    # Install prek hooks
    if Path("prek.toml").is_file():
        typer.secho("Installing prek hooks...")
        subprocess.check_call(["uv", "run", "prek", "install"])
    else:
        typer.secho("❌ No prek.toml file found. Skipping installation of prek hooks.", fg=typer.colors.YELLOW)

    typer.secho("✅ Setup complete!", fg=typer.colors.GREEN)


def _install_uv() -> None:
    """Install UV."""
    typer.secho("⏳ Installing UV...", fg=typer.colors.YELLOW)
    subprocess.check_call("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True)
    typer.secho("✅ UV installed!")


if __name__ == "__main__":
    typer.run(setup)
