import sys

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List, Dict
from src.project.tools.fire_crew_navigator_tool import FireCrewNavigatorTool

from langchain_community.llms import OpenAI, Ollama
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

agent_llm = ChatOpenAI(
    temperature=0, 
    model='gpt-4o-mini'
)

CHOSEN_LLM = agent_llm

class FirefighterPlannerSchema(BaseModel):
    """Output for the firefighter plan task"""
    personnel: Dict[str, int] = Field(..., description='Dictionary indicating personnel roles and the number of units necessary')
    vehicles: Dict[str, int] = Field(..., description='Pairs indicating types of vehicles and their quantities')
    material: List[Dict[str, int]] = Field(..., description='Pairs indicating equipment required to assess the fire and their quantities')
    route_to_fire: List[str] = Field(..., description='List of streets and numbers forming the route from the fire station to the fire incident location')
    response_time: float = Field(..., description='Time taken to go from the fire station to the fire incident location')
    reasoning: str = Field(..., description='Explanations for the decisions made.')

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
    path_file_map = 'src/project/maps/vilanova_i_la_geltru.graphml'

    def __init__(self):
        self.resources_file = 'src/project/crews/fire_crew/resources/resources1.json'
        self.resources_list_file = 'src/project/crews/fire_crew/resources/simplified_resources1.json'


    # Fire Expert Agent
    @agent
    def new_fire_expert_agent(self) -> Agent:
        simplified_resources_read_tool = FileReadTool(file_path=self.resources_list_file)
        return Agent(
            config=self.agents_config['new_fire_expert_agent'],
            verbose=True,
            allow_delegation=False,
            llm=CHOSEN_LLM,
            tools=[simplified_resources_read_tool],
            max_iter=1,
            cache=False
        )

    # Material Selector Agent
    @agent
    def material_selector_agent(self) -> Agent:
        resources_read_tool = FileReadTool(file_path=self.resources_file)
        return Agent(
            config=self.agents_config['material_selector_agent'],
            verbose=True,
            allow_delegation=False,
            llm=CHOSEN_LLM,
            tools=[resources_read_tool],
            max_iter=1,
            cache=False
        )

    # Material Navigator Agent
    @agent
    def material_navigator_agent(self) -> Agent:
        fire_crew_navigator_tool = FireCrewNavigatorTool(
            city_map_file=self.path_file_map,
            fire_station_location='Av. de Francesc Macia, 134, 08800 Vilanova i la Geltru, Barcelona'
        )
        return Agent(
            config=self.agents_config['material_navigator_agent'],
            verbose=True,
            allow_delegation=False,
            llm=CHOSEN_LLM,
            tools=[fire_crew_navigator_tool],
            max_iter=1,
            cache=False
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
            cache=False
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
                    FirefighterCrew()
                    .crew()
                    .kickoff(inputs={'FireEmergency': fire_emergency_content})
            )
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}") from e