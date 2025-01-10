import sys
import json

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List, Tuple

from tools.route_distance_tool import RouteDistanceTool
from tools.ambulance_selector_tool import AmbulanceSelectorTool

class MedicalPlannerSchema(BaseModel):
	"""Output for the medical plan task."""
	personnel_employed: List[Tuple[str, str]] = Field(..., description='Pairs of personnel identifications with its ambulance identification assigned.')
	ambulances_employed: List[str] = Field(..., description='Identifications of the ambulances employed.') # TODO: Remove?
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
class MedicalCrew:
    """Medical Services Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    path_file_map = 'maps/vilanova_i_la_geltru.graphml'
    

    def __init__(self, medical_file):
        self._medical_file = medical_file
        self._ambulance_file = 'crews/medical_crew/resources/resourcesAmbulances1.json'
        self._hospital_file = 'crews/medical_crew/resources/resourcesHospitals1.json'

    @agent
    def emergency_doctor_agent(self) -> Agent:
        file_read_tool = FileReadTool(file_path=self._medical_file)
        return Agent(
            config=self.agents_config['emergency_doctor_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            tools=[file_read_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def ambulance_selector_agent(self) -> Agent:
        with open(self._ambulance_file, "r") as f:
            ambulance_data = json.load(f)

        ambulance_selector_tool = AmbulanceSelectorTool(self.path_file_map, input=ambulance_data["ambulances"])
        file_read_tool = FileReadTool(file_path=self._medical_file)
        return Agent(
            config=self.agents_config['ambulance_selector_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            tools=[file_read_tool, ambulance_selector_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def ambulance_navigator_agent(self) -> Agent:
        ambulance_read_tool = FileReadTool(self._ambulance_file)
        distance_calculator_tool = RouteDistanceTool(self.path_file_map)
        return Agent(
            config=self.agents_config['ambulance_navigator_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            tools=[FileReadTool(self._ambulance_file)],
            max_iter=1,
            cache=False,
        )

    @agent
    def ambulance_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['ambulance_planner_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            max_iter=1,
            cache=False,
        )

    @agent
    def hospital_selector_agent(self) -> Agent:
        hospital_read_tool = FileReadTool(self._hospital_file)
        distance_calculator_tool = RouteDistanceTool(self.path_file_map)
        return Agent(
            config=self.agents_config['hospital_selector_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            tools=[hospital_read_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def hospital_navigator_agent(self) -> Agent:
        file_read_tool = FileReadTool(self._hospital_file)
        distance_calculator_tool = RouteDistanceTool(self.path_file_map)
        return Agent(
            config=self.agents_config['hospital_navigator_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            tools=[file_read_tool],
            max_iter=1,
            cache=False,
        )

    @agent
    def hospital_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['hospital_planner_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
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

    # @task
    # def medical_divide_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['medical_divide_task']
    #     )

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
    def ambulance_navigate_task(self) -> Task:
        return Task(
            config=self.tasks_config['ambulance_navigate_task']
        )

    @task
    def ambulance_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['ambulance_plan_task']
        )

    @task
    def hospital_select_task(self) -> Task:
        distance_calculator_tool = RouteDistanceTool(self.path_file_map)
        return Task(
            config=self.tasks_config['hospital_select_task'],
            tools=[distance_calculator_tool]
        )

    @task
    def hospital_navigate_task(self) -> Task:
        distance_calculator_tool = RouteDistanceTool(self.path_file_map)
        return Task(
            config=self.tasks_config['hospital_navigate_task'],
            tools=[distance_calculator_tool]
        )

    @task
    def hospital_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['hospital_plan_task']
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