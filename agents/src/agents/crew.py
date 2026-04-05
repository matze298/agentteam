"""Defines our ResearchCrew."""

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, after_kickoff, agent, before_kickoff, crew, task
from crewai_tools import SerperDevTool


@CrewBase
class LatestAiDevelopmentCrew:
    """LatestAiDevelopment crew."""

    agents: list[BaseAgent]
    tasks: list[Task]
    agents_config: dict
    tasks_config: dict

    @before_kickoff
    def before_kickoff_function(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Modify the inputs before the kickoff."""
        return inputs

    @after_kickoff
    def after_kickoff_function(self, result: dict[str, Any]) -> dict[str, Any]:
        """Modify the result after the kickoff."""
        return result

    @agent
    def researcher(self) -> Agent:
        """Creates the researcher agent."""
        return Agent(
            config=self.agents_config["researcher"],  # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()],
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Creates the reporting analyst agent."""
        return Agent(config=self.agents_config["reporting_analyst"], verbose=True)

    @task
    def research_task(self) -> Task:
        """Creates the research task."""
        return Task(config=self.tasks_config["research_task"])  # ty:ignore[missing-argument]

    @task
    def reporting_task(self) -> Task:
        """Creates the reporting task."""
        return Task(  # ty:ignore[missing-argument]
            config=self.tasks_config["reporting_task"],
            output_file="output/report.md",  # This is the file that will be contain the final report.
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LatestAiDevelopment crew."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
