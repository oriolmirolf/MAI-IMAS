import os
import sys
import json

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from typing import List, Dict

from src.project.tools.ambulance_selector_tool import AmbulanceSelectorTool
from src.project.tools.hospital_selector_tool import HospitalSelectorTool
from src.project.tools.route_navigator_tool import RouteNavigatorTool

from langchain_openai import ChatOpenAI

openai_api_key = os.getenv('OPENAI_API_KEY')

agent_llm = ChatOpenAI(
    temperature=0.1, 
    model='gpt-4o-mini',
    api_key=openai_api_key, 
    # model='gpt-3.5-turbo-1106', 
    # model='gpt-4o', 
)

class MedicalPlannerSchema(BaseModel):
	"""Output for the medical plan task."""
	person_injury: Dict[str, str] = Field(..., Description='Dictionary of person identifications with the classification of their injury (Nurse Check/Hospitalization/ICU).')
	ambulance_injured_assignations: Dict[str, str] = Field(..., description='Dictionary of ambulance identifications with the injured person identifications they are assigned.')
	ambulance_hospitals_assignations: Dict[str, str] = Field(..., description='Dictionary of ambulance identifications with the identification of the hospital assigned.')
	injured_room_assignations: Dict[str, str] = Field(..., description='Dictionary of the injured persons identifications with their assigned room identifications.')
	routes_to_fire: Dict[str, List[str]] = Field(..., description='Dictionary of ambulance identifications along with a list of their routes from their origin location to the fire emergency.')
	routes_to_hospitals: Dict[str, List[str]] = Field(..., description='Dictionary of ambulance identifications along with a list of their routes from the fire emergency to the hospital assigned.')
	ambulance_distances: Dict[str, int] = Field(..., description='Dictionary of ambulance identifications with their total travel distance.')

	@classmethod
	def get_schema(cls) -> str:
		schema = '\n'
		for field_name, field_instance in cls.model_fields.items():
			schema += f'{field_name}, described as: {field_instance.description}\n'
		return schema

@CrewBase
class MedicalCrew:
    """Medical Services Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    path_file_map = 'src/project/maps/vilanova_i_la_geltru.graphml'
    

    def __init__(self):
        #self._emergency_output = emergency_output
        self._ambulance_file = 'src/project/crews/medical_crew/resources/resourcesAmbulances1.json'
        self._hospital_file = 'src/project/crews/medical_crew/resources/resourcesHospitals1.json'

    @agent
    def emergency_doctor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['emergency_doctor_agent'],
            verbose=True,
            allow_delegation=False,
            llm=agent_llm,
            max_iter=1,
            cache=False,
        )

    @agent
    def ambulance_selector_agent(self) -> Agent:
        with open(self._ambulance_file, "r") as f:
            ambulance_data = json.load(f)

        ambulance_selector_tool = AmbulanceSelectorTool(self.path_file_map, input=ambulance_data["ambulances"])
        return Agent(
            config=self.agents_config['ambulance_selector_agent'],
            verbose=True,
            allow_delegation=False,
            llm=agent_llm,
            tools=[ambulance_selector_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def hospital_assigner_agent(self) -> Agent:
        with open(self._hospital_file, "r") as f:
            hospital_data = json.load(f)

        hospital_selector_tool = HospitalSelectorTool(self.path_file_map, hospital_data)
        return Agent(
            config=self.agents_config['hospital_assigner_agent'],
            verbose=True,
            allow_delegation=False,
            llm=agent_llm,
            tools=[hospital_selector_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def route_navigator_agent(self) -> Agent:
        route_navigator_tool = RouteNavigatorTool(self.path_file_map)
        return Agent(
            config=self.agents_config['route_navigator_agent'],
            verbose=True,
            allow_delegation=False,
            llm=agent_llm,
            tools=[route_navigator_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def medical_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['medical_planner_agent'],
            verbose=True,
            allow_delegation=False,
            llm=agent_llm,
            max_iter=1,
            cache=False,
        )
    
    @task
    def emergency_doctor_task(self) -> Task:
        return Task(
			config=self.tasks_config['emergency_doctor_task']
		)

    @task
    def ambulance_select_task(self) -> Task:
        return Task(
            config=self.tasks_config['ambulance_select_task']
        )

    @task
    def hospital_assign_task(self) -> Task:
        return Task(
            config=self.tasks_config['hospital_assign_task']
        )

    @task
    def route_navigate_task(self) -> Task:
        return Task(
            config=self.tasks_config['route_navigate_task']
        )

    @task
    def medical_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['medical_plan_task'],
            output_pydantic=MedicalPlannerSchema
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Medical Services Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )

if __name__ == '__main__':
    result = (
          MedicalCrew(sys.argv[1])
          .crew()
          .kickoff()
	)