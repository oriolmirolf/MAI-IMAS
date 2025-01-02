from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List



class FirefighterPlannerSchema(BaseModel):
	"""Output for the firefighter plan task"""
	# TODO: Identification or type of vehicle. More than one vehicle of the same type?
	personnel: List[(str, str)] = Field(..., description='Pairs of personnel identifications with its vehicle identification assigned.')
	vehicles_emplyed: List[(str, str)] = Field(..., description='Type of vehicles employed, along with its identification')
	material: List[(str, int)] = Field(..., description='List of materials that must be carried to assess the fire, along with its quanitity.')
	route_to_fire: List[(float, float)] = Field(..., description='List with X and Y coordinates that form the route from the firefighter station to the fire incident location.')
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

	def __init__(self, emergency_file):
		self._emergency_file = emergency_file

	@agent
	def firefighter_divider_agent(self) -> Agent:
		file_read_tool = FileReadTool(self._emergency_file)
		return Agent(
			config=self.agents_config['firefighter_divider_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[file_read_tool],
			max_iter=1,
		)
	
	# @agent
	# def fire_expert_agent(self) -> Agent:
	# 	return Agent(
	# 		config=self.agents_config['fire_expert_agent'],
	# 		verbose=True,
	# 		allow_delegation=False,
	# 		llm='ollama/llama3.1',
	# 		max_iter=1,
	# 	)

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def firefighter_divider_task(self) -> Task:
		return Task(
			config=self.tasks_config['firefighter_divider_task'],
		)
	
	# @task
	# def divide_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['divide_task'],
	# 		output_pydantic=DividedInformationSchema
	# 	)
	
	

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
