import networkx
import json
import osmnx as ox
from crewai_tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

class RouteDistanceSchema(BaseModel):
    """Input schema for the Route Distance Calculator Tool."""
    origin_location: str = Field(..., description='Address of the origin location.')
    destination_location: str = Field(..., description='Address of the destination location.')

class RouteDistanceTool(BaseTool):
    name: str = 'Route Distance Calculator'
    description: str = 'A tool to find the shortest distance between an origin and destination location.'
    args_schema: Type[BaseModel] = RouteDistanceSchema
    city_map: networkx.classes.multidigraph.MultiDiGraph = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map: str, **kwargs):
        super().__init__(**kwargs)

        self.city_map = ox.load_graphml(city_map)
        self.city_map = ox.routing.add_edge_speeds(self.city_map)
        self.city_map = ox.routing.add_edge_travel_times(self.city_map)
    
    def _run(self, *args) -> int:
        print(f'Args is {args}')
        if not args:
            raise ValueError(
                "No arguments provided to RouteDistanceTool. "
                "You must provide a JSON string with 'origin_location' and 'destination_location'."
            )
        
        input_str = args[0]

        try:
            # Parse the JSON string into a dictionary
            input_data = json.loads(input_str)
            print("Parsed input data:", input_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        # Extract locations from the parsed data
        origin_location = input_str.get('origin_location')
        origin_coordinates = ox.geocode(origin_location)
        
        x_origin, y_origin = origin_coordinates[1], origin_coordinates[0]

        destination_location = args.input_str('destination_location')
        destination_coordinates = ox.geocode(destination_location)

        x_destination, y_destination = destination_coordinates[1], destination_coordinates[0]
        
        return self._find_distance(x_origin, y_origin, x_destination, y_destination)

    def _find_distance(self, x_origin: float, y_origin: float, x_destination: float, y_destination: float) -> int:
        origin_node = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
        destination_node = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)
        route = ox.shortest_path(self.city_map, origin_node, destination_node, weight='travel_time')
        edge_lengths = ox.routing.route_to_gdf(self.city_map, route)['length']

        return round(sum(edge_lengths))