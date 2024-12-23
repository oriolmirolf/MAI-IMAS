from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Emergency():
	"""Emergency crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def content_planner(self) -> Agent:
		return Agent(
			config=self.agents_config['content_planner'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1'
		)

	@agent
	def content_writter(self) -> Agent:
		return Agent(
			config=self.agents_config['content_writter'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1'
		)
	
	@agent
	def content_editor(self) -> Agent:
		return Agent(
			config=self.agents_config['content_editor'],
			verbose=True,
			allow_delegation=False,
			llm='ollama/llama3.1'
		)

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def planning_task(self) -> Task:
		return Task(
			config=self.tasks_config['planning_task'],
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
			output_file='report.md'
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
