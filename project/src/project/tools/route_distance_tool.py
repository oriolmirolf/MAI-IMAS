import networkx
import json
import osmnx as ox
from crewai_tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
from typing import Any

class RouteDistanceSchema(BaseModel):
    """Input schema for the Route Distance Calculator Tool."""
    origin_location: Any = Field(..., description='Address of the origin location.')
    destination_location: str = Field(..., description='Address of the destination location.')

class RouteDistanceTool(BaseTool):
    name: str = 'Route Distance Calculator'
    description: str = 'This tool calculates the shortest route distance between two locations.'
    args_schema: Type[BaseModel] = RouteDistanceSchema
    city_map: networkx.classes.multidigraph.MultiDiGraph = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map: str, **kwargs):
        super().__init__(**kwargs)

        self.city_map = ox.load_graphml(city_map)
        self.city_map = ox.routing.add_edge_speeds(self.city_map)
        self.city_map = ox.routing.add_edge_travel_times(self.city_map)
    
    def _run(self, origin_location: str, destination_location: str) -> int: # Output in meters
        origin_coordinates = ox.geocode(origin_location)
        x_origin, y_origin = origin_coordinates[1], origin_coordinates[0]

        destination_coordinates = ox.geocode(destination_location)
        x_destination, y_destination = destination_coordinates[1], destination_coordinates[0]
        
        return self._find_distance(x_origin, y_origin, x_destination, y_destination)

    def _find_distance(self, x_origin: float, y_origin: float, x_destination: float, y_destination: float) -> int:
        origin_node = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
        destination_node = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)
        if origin_node == destination_node:
            return 0
        route = ox.shortest_path(self.city_map, origin_node, destination_node, weight='travel_time')
        edge_lengths = ox.routing.route_to_gdf(self.city_map, route)['length']

        return round(sum(edge_lengths))