from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List

from tools.route_distance_tool import RouteDistanceTool

class MedicalPlannerSchema(BaseModel):
	"""Output for the medical plan task."""
	personnel_employed: List[(str, str)] = Field(..., description='Pairs of personnel identifications with its ambulance identification assigned.')
	ambulances_employed: List[str] = Field(..., description='Identifications of the ambulances employed.') # ToDo: Remove?
	#materials_required: # ToDo: Include?
	assigned_hospitals: List[(str, str)] = Field(..., description='Pairs of ambulance identifications with its hospital identification assigned.')
	rooms_needed: List[(str, List[str])] = Field(..., description='Pairs of hospital identifications with a list of rooms identifications needed for that hospital.')
	routes_to_fire: List[(float, float)] = Field(..., description='List of ambulance identifications along with the X and Y coordinates that form the route for that hospital from their current location to the fire scene.')
	routes_to_hospitals: List[str, List[(float, float)]] = Field(..., description='List of ambulance identifications along with the X and Y coordinates that form the route from the fire scene to the assigned hospital.')
	response_time: List[str, int] = Field(..., description=('Pairs of ambulance identifications and their time taken to reach the fire scene.'))

	@classmethod
	def get_schema(cls) -> str:
		schema = '\n'
		for field_name, field_instance in cls.model_fields.items():
			schema += f'{field_name}, described as: {field_instance.description}\n'
		return schema

@CrewBase
class MedicalCrew():
	"""Medical Services Crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'
	path_file_map = '../../maps/sitges.graphml'

	def __init__(self, medical_file):
		self._medical_file = medical_file

    @agent
    def medical_divider_agent(self) -> Agent:
		file_read_tool = FileReadTool(self._medical_file)
		return Agent(
			config=self.agents_config['medical_divider_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[file_read_tool],
			max_iter=1,
		)

    @agent
    def ambulance_selector_agent(self) -> Agent:
		distance_calculator_tool = RouteDistanceTool(self.path_file_map)
		return Agent(
			config=self.agents_config['ambulance_selector_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[distance_calculator_tool],
			max_iter=1,
		)

    @agent
	def ambulance_navigator_agent(self) -> Agent:
		distance_calculator_tool = RouteDistanceTool(self.path_file_map)
		return Agent(
			config=self.agents_config['ambulance_navigator_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[distance_calculator_tool],
			max_iter=1,
		)

    @agent
	def ambulance_planner_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['ambulance_planner_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			max_iter=1,
		)

    @agent
    def hospital_selector_agent(self) -> Agent:
		distance_calculator_tool = RouteDistanceTool(self.path_file_map)
		return Agent(
			config=self.agents_config['hospital_selector_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[distance_calculator_tool],
			max_iter=1,
		)

    @agent
	def hospital_navigator_agent(self) -> Agent:
		distance_calculator_tool = RouteDistanceTool(self.path_file_map)
		return Agent(
			config=self.agents_config['hospital_navigator_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[distance_calculator_tool],
			max_iter=1,
		)

    @agent
	def hospital_planner_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['hospital_planner_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			max_iter=1,
		)

    @agent
	def medical_planner_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['medical_planner_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			max_iter=1,
		)

    @task
	def medical_divide_task(self) -> Task:
		return Task(
			config=self.tasks_config['medical_divide_task']
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
		return Task(
			config=self.tasks_config['hospital_select_task']
		)

    @task
	def hospital_navigate_task(self) -> Task:
		return Task(
			config=self.tasks_config['hospital_navigate_task']
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
		"""Creates the Medical Services crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)