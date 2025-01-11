#!/usr/bin/env python
import sys
import json

from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, router, or_, and_

from .crews.emergency_crew.emergency_crew import EmergencyCrew
from .crews.medical_crew.medical_crew import MedicalCrew
from .crews.fire_crew.fire_crew import FirefighterCrew
from .crews.reporter_crew.reporter_crew import ReporterCrew

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
        result = (
            EmergencyCrew(self.state.emergency_file)
            .crew()
            .kickoff()
        )
        # split the fields into data relevant for medical and data relevant for firefighters
        info_json = json.loads(result.raw)
        try:
            self.state.medical_services_needed = bool(info_json["medical_services_needed"])
        except:
            self.state.medical_services_needed = True
        try:
            info_medical = {
                "emergency_location": info_json["emergency_location"],
                "number_injured_people": info_json["number_injured_people"],
                "injury_level": [f"ID{i} {il}" for i, il in enumerate(info_json["injury_level"])],
                "extra_information_medical": info_json["extra_information_medical"],
            }
            if info_medical["number_injured_people"] == 0:
                info_medical["injury_level"] = []
            self.state.info_medical = json.dumps(info_medical, indent=2)
        except:
            self.state.info_medical = result.raw
        try:
            info_fire = {
                "fire_severity": info_json["fire_severity"],
                "fire_type": info_json["fire_type"],
                "emergency_location": info_json["emergency_location"],
                "extra_information_fire": info_json["extra_information_fire"],
            }
            self.state.info_fire = json.dumps(info_fire, indent=2)
        except:
            self.state.info_fire = result.raw
        print()
        print(self.state.info_medical)
        print()
        print(self.state.info_fire)
    
    @router(emergency_crew)
    def router_medical_needed(self):
        if self.state.medical_services_needed:
            return "medical-needed"
        else:
            return "medical-not-needed"
    
    @listen("medical-needed")
    def medical_crew(self):
        print("EXECUTING MEDICAL CREW")
        self.state.medical_planning = MedicalCrew(self.state.info_medical).crew().kickoff()
    
    @listen("medical-not-needed")
    def no_medical_crew(self):
        print("NO MEDICAL CREW NEEDED")
        self.state.medical_planning = '{"medical_services_needed": "false"}'
    
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
