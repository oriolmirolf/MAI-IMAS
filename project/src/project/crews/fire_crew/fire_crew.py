import sys
# from jinja2 import Template
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List, Tuple
from tools.fire_crew_navigator_tool import FireCrewNavigatorTool

from langchain_community.llms import OpenAI, Ollama
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI



agent_llm = ChatOpenAI(
    temperature=0, 
    # model='gpt-3.5-turbo', 
    model='gpt-4o-mini'
    )

CHOSEN_LLM = agent_llm

class FirefighterPlannerSchema(BaseModel):
    """Output for the firefighter plan task"""
    personnel: List[Tuple[str, int]] = Field(..., description='Pairs indicating personnel roles and the number of units necessary')
    vehicles: List[Tuple[str, int]] = Field(..., description='Pairs indicating types of vehicles and their quantities')
    material: List[Tuple[str, int]] = Field(..., description='Pairs indicating equipment required to assess the fire and their quantities')
    route_to_fire: List[str] = Field(..., description='List of streets and numbers forming the route from the fire station to the fire incident location')
    response_time: float = Field(..., description='Time taken to go from the fire station to the fire incident location')
    resoning: str = Field(..., description='Explanations for the decisions made.')

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
    path_file_map = 'maps/vilanova_i_la_geltru.graphml'

    def __init__(self, emergency_file):
        self._emergency_file = emergency_file
        self.resources_file = 'crews/fire_crew/resources/resources1.json'

    # Fire Expert Agent
    @agent
    def new_fire_expert_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['new_fire_expert_agent'],
            verbose=True,
            allow_delegation=False,
            llm=CHOSEN_LLM,
            max_iter=1,
        )

    # Material Selector Agent
    @agent
    def material_selector_agent(self) -> Agent:
        # file_read_tool = FileReadTool(file_path=self._emergency_file)
        resources_read_tool = FileReadTool(file_path=self.resources_file)
        return Agent(
            config=self.agents_config['material_selector_agent'],
            verbose=True,
            allow_delegation=False,
            llm=CHOSEN_LLM,
            tools=[resources_read_tool],
            max_iter=1,
        )

    # Material Navigator Agent
    @agent
    def material_navigator_agent(self) -> Agent:
        fire_crew_navigator_tool = FireCrewNavigatorTool(
            city_map_file=self.path_file_map,
            fire_station_location='Av. de Francesc Macià, 134, 08800 Vilanova i la Geltrú, Barcelona'
        )
        return Agent(
            config=self.agents_config['material_navigator_agent'],
            verbose=True,
            allow_delegation=False,
            llm=CHOSEN_LLM,
            tools=[fire_crew_navigator_tool],
            max_iter=1,
        )

    # Firefighter Planner Agent
    @agent
    def firefighter_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['firefighter_planner_agent'],
            verbose=True,
            allow_delegation=False,
            llm=CHOSEN_LLM,
            max_iter=1,
        )

    # Tasks
    @task
    def new_fire_expert_task(self) -> Task:
        return Task(
            config=self.tasks_config['new_fire_expert_task']
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
    def firefighter_planner_task(self) -> Task:
        return Task(
            config=self.tasks_config['firefighter_planner_task'],
            output_pydantic=FirefighterPlannerSchema
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Firefighter crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )


if __name__ == "__main__":
    try:
        with open(sys.argv[1], 'r') as file:
            fire_emergency_content = file.read().strip()
            result = (
                    FirefighterCrew(sys.argv[1])
                    .crew()
                    .kickoff(inputs={'FireEmergency': fire_emergency_content})
            )
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}") from e