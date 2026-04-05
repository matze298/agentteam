"""Entrypoint for Agent deployment."""

from agents.crew import LatestAiDevelopmentCrew
from security.docker import ensure_docker_running


def run() -> None:
    """Run the crew."""
    inputs = {"topic": "Cycling Training plan"}
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    ensure_docker_running()
    run()
