from agents.crew import LatestAiDevelopmentCrew


def run():
    """Run the crew."""
    inputs = {"topic": "Cycling Training plan"}
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
