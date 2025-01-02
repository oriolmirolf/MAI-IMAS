from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List

@CrewBase
class MedicalCrew():
	"""Medical crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, medical_file):
		self._medical_file = medical_file