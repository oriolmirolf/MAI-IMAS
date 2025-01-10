import sys
import json

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List, Tuple

from tools.ambulance_selector_tool import AmbulanceSelectorTool
from tools.hospital_selector_tool import HospitalSelectorTool
from tools.route_navigator_tool import RouteNavigatorTool
from tools.route_distance_tool import RouteDistanceTool


class MedicalPlannerSchema2(BaseModel):
	"""Output for the medical plan task."""
	ambulances_employed: List[str] = Field(..., description='Pairs of ambulance identifications with the injured person identfications assigned.')
	assigned_hospitals: List[Tuple[str, str]] = Field(..., description='Pairs of ambulance identifications with its hospital identification assigned.')
	rooms_needed: List[Tuple[str, List[str]]] = Field(..., description='Pairs of hospital identifications with a list of rooms identifications needed for that hospital.')
	routes_to_fire: List[Tuple[float, float]] = Field(..., description='List of ambulance identifications along with the X and Y coordinates that form the route for that hospital from their current location to the fire scene.')
	routes_to_hospitals: List[Tuple[str, List[Tuple[float, float]]]] = Field(..., description='List of ambulance identifications along with the X and Y coordinates that form the route from the fire scene to the assigned hospital.')
	response_time: List[Tuple[str, int]] = Field(..., description=('Pairs of ambulance identifications and their time taken to reach the fire scene.'))

	@classmethod
	def get_schema(cls) -> str:
		schema = '\n'
		for field_name, field_instance in cls.model_fields.items():
			schema += f'{field_name}, described as: {field_instance.description}\n'
		return schema

@CrewBase
class MedicalCrew2:
    """Medical Services Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    path_file_map = 'maps/vilanova_i_la_geltru.graphml'
    

    def __init__(self, medical_file):
        self._medical_file = medical_file
        self._ambulance_file = 'crews/medical_crew/resources/resourcesAmbulances1.json'
        self._hospital_file = 'crews/medical_crew/resources/resourcesHospitals1.json'
        self._prev_answer = 'crews/medical_crew/resources/answer_hospital_assigner.txt'

    @agent
    def route_navigator_agent(self) -> Agent:
        previous_answer = FileReadTool(self._prev_answer)
        file_read_tool = FileReadTool(self._hospital_file)
        route_navigator_tool = RouteNavigatorTool(self.path_file_map)
        return Agent(
            config=self.agents_config['route_navigator_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            tools=[previous_answer, route_navigator_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def medical_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['medical_planner_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            max_iter=1,
            cache=False,
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
            output_pydantic=MedicalPlannerSchema2
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Medical Services Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder={
                "provider": "ollama",
                "config": {
                    "model": "mxbai-embed-large"
                }
            }
        )

if __name__ == '__main__':
    result = (
          MedicalCrew2(sys.argv[1])
          .crew()
          .kickoff()
	)