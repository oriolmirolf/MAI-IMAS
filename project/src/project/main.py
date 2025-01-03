#!/usr/bin/env python
import sys
import json

from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, router, or_, and_

from .crews.emergency_crew.emergency_crew import EmergencyCrew


class ProjectState(BaseModel):
    emergency_file: str = "./tests/test4.txt"
    medical_services_needed: bool = True
    info_medical: str = ""
    info_fire: str = ""
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
        # split the fields into data relevant for medical and data relevant for firefighters
        info_json = json.loads(result.raw)
        self.state.medical_services_needed = bool(info_json["medical_services_needed"])
        info_medical = {
            "emergency_location": info_json["emergency_location"],
            "number_injured_people": info_json["number_injured_people"],
            "injury_level": info_json["injury_level"],
            "extra_information_medical": info_json["extra_information_medical"],
        }
        info_fire = {
            "fire_severity": info_json["fire_severity"],
            "fire_type": info_json["fire_type"],
            "emergency_location": info_json["emergency_location"],
            "extra_information_fire": info_json["extra_information_fire"],
        }
        self.state.info_medical = json.dumps(info_medical, indent=2)
        self.state.info_fire    = json.dumps(info_fire, indent=2)
        print("----------")
        print(self.state.info_fire)
        print("----------")
        print(self.state.info_medical)
    
    @router(emergency_crew)
    def router_medical_needed(self):
        if self.state.medical_services_needed:
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
