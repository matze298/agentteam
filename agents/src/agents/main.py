"""Entrypoint for Agent deployment."""

from agents.crew import LatestAiDevelopmentCrew


def run() -> None:
    """Run the crew."""
    inputs = {"topic": "Cycling Training plan"}
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
