import sys

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool

from langchain_openai import ChatOpenAI

agent_llm = ChatOpenAI(
    temperature=0.1, 
    model='gpt-4o'#-mini'
)

@CrewBase
class ReporterCrew():
	"""Reporter crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, input_file=""):
		self._emergency_file = input_file

	@agent
	def writer_agent(self) -> Agent:
		tools = []
		if self._emergency_file:
			tools = [FileReadTool(self._emergency_file)]
		else:
			tools = []
		return Agent(
			config=self.agents_config['writer_agent'],
			verbose=True,
			allow_delegation=False,
			llm=agent_llm,
			tools=tools,
			max_iter=1,
		)
	
	@agent
	def editor_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['editor_agent'],
			verbose=True,
			allow_delegation=False,
			llm=agent_llm,
		)

	@task
	def writing_task(self) -> Task:
		return Task(
			config=self.tasks_config['writing_task'],
		)
	
	@task
	def editing_task(self) -> Task:
		return Task(
			config=self.tasks_config['editing_task'],
		)	


	@crew
	def crew(self) -> Crew:
		"""Creates the Emergency crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)

if __name__ == "__main__":

	def fileContents(fname):
		with open(fname) as f:
			contents = f.read()
		return contents

	inputs = {
		"firefighter_data": fileContents(sys.argv[1]),
		"medical_data": fileContents(sys.argv[2]),
		"original_call": fileContents(sys.argv[3])
	}
	result = (
			ReporterCrew()
			.crew()
			.kickoff(inputs=inputs)
	)
	print("------------")
	print(result.raw)