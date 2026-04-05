"""Functionality to ensure the Crew is running in a Docker."""

import logging
import subprocess
import sys

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def ensure_docker_running() -> None:
    """Executes a subprocess call to verify the Docker daemon is active.

    Exits the script immediately if Docker is offline or not installed.
    """
    try:
        # We run 'docker info' and pipe stdout/stderr to DEVNULL to keep the terminal clean
        result = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        if result.returncode != 0:
            _LOGGER.exception("🛑 CRITICAL SECURITY HALT: Docker daemon is not running!")
            _LOGGER.exception("The CodeInterpreterTool requires Docker to sandbox code execution safely.")
            _LOGGER.exception("Please start Docker Desktop or the Docker service and try again.")
            sys.exit(1)

        _LOGGER.info("✅ Security Check Passed: Docker daemon is active. Safe to proceed.")

    except FileNotFoundError:
        _LOGGER.exception("🛑 CRITICAL SECURITY HALT: Docker is not installed or not in PATH!")
        _LOGGER.exception("Install Docker before running AI agents with code execution capabilities.")
        sys.exit(1)


if __name__ == "__main__":
    ensure_docker_running()
