import sys
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List, Tuple



class FirefighterPlannerSchema(BaseModel):
	"""Output for the firefighter plan task"""
	# TODO: Identification or type of vehicle. More than one vehicle of the same type?
	personnel: List[Tuple[str, int]] = Field(..., description='Pairs of personnel types and its number of units')
	#personnel: List[(str, str)] = Field(..., description='Pairs of personnel identifications with its vehicle identification assigned.')
	vehciles: List[Tuple[str, int]] = Field(..., description='Pairs of vehicle types and its quantity')
	material: List[Tuple[str, int]] = Field(..., description='Pairs of equipment that must be carried to assess the fire, along with its quanitity.')
	route_to_fire: List[Tuple[float, float]] = Field(..., description='List with X and Y coordinates that form the route from the firefighter station to the fire incident location.')
	response_time: float = Field(..., description='Time taken to go from the firefighter station to the fire incident location.')

	@classmethod
	def get_schema(cls) -> str:
		schema = '\n'
		for field_name, field_instance in cls.model_fields.items():
			schema += f'{field_name}, described as: {field_instance.description}\n'
		return schema



@CrewBase
class FirefighterCrew():
	"""Firefighter crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, emergency_file, resources_file):
		self._emergency_file = emergency_file
		self._resources_file = resources_file

	@agent
	def firefighter_divider_agent(self) -> Agent:
		file_read_tool = FileReadTool(file_path=self._emergency_file)
		resources_read_tool = FileReadTool(file_path=self._resources_file)
		return Agent(
			config=self.agents_config['firefighter_divider_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[file_read_tool, resources_read_tool],
			max_iter=1,
		)
	
	@agent
	def fire_expert_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['fire_expert_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			max_iter=1,
		)
	
	@agent
	def firefighter_planner_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['firefighter_planner_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			max_iter=1,
		)


	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def firefighter_divider_task(self) -> Task:
		return Task(
			config=self.tasks_config['firefighter_divider_task'],
		)
	
	@task
	def fire_expert_task(self) -> Task:
		return Task(
			config=self.tasks_config['fire_expert_task'],
		)
	
	@task
	def firefighter_planner_task(self) -> Task:
		return Task(
			config=self.tasks_config['firefighter_planner_task'],
			output_pydantic=FirefighterPlannerSchema
		)
	
	

	@crew
	def crew(self) -> Crew:
		"""Creates the Emergency crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)


if __name__ == "__main__":
	result = (
			FirefighterCrew(sys.argv[1], sys.argv[2])
			.crew()
			.kickoff()
	)