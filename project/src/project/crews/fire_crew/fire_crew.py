from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List
from tools.route_distance_tool import RouteDistanceTool

class FirefighterPlannerSchema(BaseModel):
    """Output for the firefighter plan task"""
    personnel: List[tuple] = Field(..., description='Pairs of personnel types and their number of units')
    vehicles: List[tuple] = Field(..., description='Pairs of vehicle types and their quantities')
    material: List[tuple] = Field(..., description='Pairs of equipment that must be carried to assess the fire, along with their quantities.')
    route_to_fire: List[tuple] = Field(..., description='List of (X, Y) coordinates forming the route from the firefighter station to the fire incident location.')
    response_time: float = Field(..., description='Time taken to go from the firefighter station to the fire incident location.')

    @classmethod
    def get_schema(cls) -> str:
        schema = '\n'
        for field_name, field_instance in cls.model_fields.items():
            schema += f'{field_name}, described as: {field_instance.description}\n'
        return schema

@CrewBase
class FirefighterCrew:
    """Firefighter crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    path_file_map = '../../maps/vilanova_i_la_geltru.graphml'

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
    def material_selector_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['material_selector_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            max_iter=1,
        )

    @agent
    def material_navigator_agent(self) -> Agent:
        distance_calculator_tool = RouteDistanceTool(self.path_file_map)
        return Agent(
            config=self.agents_config['material_navigator_agent'],
            verbose=True,
            allow_delegation=False,
            llm='ollama/llama3.1',
            tools=[distance_calculator_tool],
            max_iter=1,
        )

    @agent
    def material_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['material_planner_agent'],
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

    # Tasks
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
    def material_select_task(self) -> Task:
        return Task(
            config=self.tasks_config['material_select_task'],
        )

    @task
    def material_navigate_task(self) -> Task:
        return Task(
            config=self.tasks_config['material_navigate_task'],
        )

    @task
    def material_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['material_plan_task'],
        )
    
    @task
    def firefighter_planner_task(self) -> Task:
        return Task(
            config=self.tasks_config['firefighter_planner_task'],
            output_pydantic=FirefighterPlannerSchema
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Firefighter crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
