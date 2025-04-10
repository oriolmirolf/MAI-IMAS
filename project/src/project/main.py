import sys
import json

from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, router, or_, and_

from src.project.crews.emergency_crew.emergency_crew import EmergencyCrew
from src.project.crews.medical_crew.medical_crew import MedicalCrew
from src.project.crews.fire_crew.fire_crew import FirefighterCrew
from src.project.crews.reporter_crew.reporter_crew import ReporterCrew

class ProjectState(BaseModel):
    emergency_file: str = "./tests/test3.txt"
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
    async def medical_crew(self):
        print("EXECUTING MEDICAL CREW")
        print(self.state.info_medical)
        medical_inputs = {'FireEmergency': self.state.info_medical}
        self.state.medical_planning = await MedicalCrew().crew().kickoff_async(inputs=medical_inputs)
    
    @listen("medical-not-needed")
    def no_medical_crew(self):
        print("NO MEDICAL CREW NEEDED")
        self.state.medical_planning = '{"medical_services_needed": "false"}'
    
    @listen(or_(medical_crew, no_medical_crew))
    def medical_output(self):
        return
    
    @listen(or_(medical_crew, no_medical_crew))
    async def firefighter_crew(self):
        print("RUNNING FIREFIGHTER CREW")
        fire_inputs = {'FireEmergency': self.state.info_fire}
        self.state.firefighter_planning = await FirefighterCrew().crew().kickoff_async(inputs=fire_inputs)
    
    @listen(and_(medical_output, firefighter_crew))
    def reporter_crew(self):
        print("RUNNING REPORTER CREW")
        def fileContents(fname):
            with open(fname) as f:
                contents = f.read()
            return contents
        inputs = {
            "firefighter_data": self.state.firefighter_planning,
            "medical_data": self.state.medical_planning,
            "original_call": fileContents(self.state.emergency_file)
        }
        result = (
                ReporterCrew()
                .crew()
                .kickoff(inputs=inputs)
        )
        self.state.final_plan = result.raw

    @listen(emergency_crew)
    def save_plan(self):
        print("   ==== OUTPUTS SUMMARY ====\n")

        print("  EMERGENCY CREW")
        print(self.state.info_fire)
        print(self.state.info_medical)

        print("\n\n  FIRE CREW")
        print(self.state.firefighter_planning)

        print("\n\n  MEDICAL CREW")
        print(self.state.medical_planning)

        print("\n\n  REPORT CREW")
        print(self.state.final_plan)

        print("\n\nSaving plan.")
        with open("plan.md", "w") as f:
            f.write(self.state.final_plan)
        print("Plan saved.")


def kickoff():
    poem_flow = ProjectFlow()
    poem_flow.kickoff()


def plot():
    poem_flow = ProjectFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
