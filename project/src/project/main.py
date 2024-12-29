#!/usr/bin/env python
import sys

from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start

from .crews.emergency_crew.emergency_crew import EmergencyCrew


class ProjectState(BaseModel):
    emergency_file: str = "./tests/test1.txt"
    divided_info: str = ""
    final_plan: str = ""


class ProjectFlow(Flow[ProjectState]):

    @start()
    def emergency_crew(self):
        print("Generating poem")
        result = (
            EmergencyCrew(self.state.emergency_file)
            .crew()
            .kickoff()
        )

        self.state.divided_info = result.raw
        self.state.final_plan = result.raw

    @listen(emergency_crew)
    def save_plan(self):
        print("Saving plan")
        with open("plan.md", "w") as f:
            f.write(self.state.final_plan)


def kickoff():
    poem_flow = ProjectFlow()
    poem_flow.kickoff()


def plot():
    poem_flow = ProjectFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
