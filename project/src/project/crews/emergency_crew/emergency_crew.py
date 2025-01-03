from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List



class DistilledEmergencyCallSchema(BaseModel):
	"""Output for the distill task."""
	fire_severity: str = Field(..., description='Severity of the fire (light, moderate, severe, extreme).')
	fire_type: str = Field(..., description='Type of fire (ordinary, electrical, gas, chemical or other types).')
	emergency_location: str = Field(..., description='Location of the emergency.')
	number_injured_people: int = Field(..., description='How many people are injured.')
	injury_level: List[str] = Field(..., description="How severe are each person's injuries.")
	extra_information: List[str] = Field(..., description="Extra information not included previously.")

	@classmethod
	def get_schema(cls) -> str:
		schema = '\n'
		for field_name, field_instance in cls.model_fields.items():
			schema += f'{field_name}, described as: {field_instance.description}\n'
		return schema


class DividedInformationSchema(BaseModel):
	"""Output for the divide task."""
	emergency_location: str = Field(..., description='Location of the emergency.')
	medical_services_needed: bool = Field(..., description="Medical emergency services are needed to treat injured people.")
	information_for_medical: List[str] = Field(..., description="Information that the medical department needs.")
	information_for_fire: List[str] = Field(..., description="Information that the fire department needs.")

	@classmethod
	def get_schema(cls) -> str:
		schema = '\n'
		for field_name, field_instance in cls.model_fields.items():
			schema += f'{field_name}, described as: {field_instance.description}\n'
		return schema


@CrewBase
class EmergencyCrew():
	"""Emergency crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, emergency_file):
		self._emergency_file = emergency_file

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def distiller_agent(self) -> Agent:
		file_read_tool = FileReadTool(self._emergency_file)
		return Agent(
			config=self.agents_config['distiller_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			tools=[file_read_tool],
			max_iter=1,
		)

	@agent
	def people_identifier_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['people_identifier_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			max_iter=1,
		)
	
	@agent
	def divider_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['divider_agent'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1',
			max_iter=1,
		)

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def distill_task(self) -> Task:
		return Task(
			config=self.tasks_config['distill_task'],
			output_pydantic=DistilledEmergencyCallSchema
		)
	
	@task
	def people_identification_task(self) -> Task:
		return Task(
			config=self.tasks_config['people_identification_task'],
			output_pydantic=DistilledEmergencyCallSchema
		)
	
	@task
	def divide_task(self) -> Task:
		return Task(
			config=self.tasks_config['divide_task'],
			output_pydantic=DividedInformationSchema
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
