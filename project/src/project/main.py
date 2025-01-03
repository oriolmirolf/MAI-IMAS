#!/usr/bin/env python
import sys
import json

from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, router, or_, and_

from .crews.emergency_crew.emergency_crew import EmergencyCrew


class ProjectState(BaseModel):
    emergency_file: str = "./tests/test4.txt"
    divided_info: str = ""
    medical_planning: str = ""
    firefighter_planning: str = ""
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
    
    @router(emergency_crew)
    def router_medical_needed(self):
        #print(f"Medical services needed: {json.loads(self.state.divided_info)["medical_services_needed"]}")
        if bool(json.loads(self.state.divided_info)["medical_services_needed"]):
            return "medical-needed"
        else:
            return "medical-not-needed"
    
    @listen("medical-needed")
    def medical_crew(self):
        print("EXECUTING MEDICAL CREW")
        # Medical crew stuff goes in here
        self.state.medical_planning = "bla bla bla medical plan"
    
    @listen("medical-not-needed")
    def no_medical_crew(self):
        print("NO MEDICAL CREW NEEDED")
        self.state.medical_planning = "{medical_services_needed: false}"
    
    @listen(or_(medical_crew, no_medical_crew))
    def medical_output(self):
        return
    
    @listen(emergency_crew)
    def firefighter_crew(self):
        print("RUNNING FIREFIGHTER CREW")
        # Firefighter crew stuff goes in here
        self.state.firefighter_planning = "bla bla bla firefighter plan"
    
    @listen(and_(medical_output, firefighter_crew))
    def reporter_crew(self):
        print("RUNNING REPORTER CREW")
        self.state.final_plan = f"final emergency plan: {self.state.medical_planning} + {self.state.firefighter_planning}"

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
