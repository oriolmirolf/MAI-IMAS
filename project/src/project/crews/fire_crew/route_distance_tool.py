import networkx
import osmnx as ox
from crewai.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

class RouteDistanceSchema(BaseModel):
    """Input for the RouteDistanceTool."""
    x_origin: float = Field(..., description='X coordinate of the origin location.')
    y_origin: float = Field(..., description='Y coordinate of the origin location.')
    x_destination: float = Field(..., description='X coordinate of the destination location.')
    y_destination: float = Field(..., description='Y coordinate of the destination location.')

class RouteDistanceTool(BaseTool):
    name: str = 'Route distance calculator'
    description: str = 'A tool to find the driving route distance between an origin and a destination in a map given their coordinates.'
    args_schema: Type[BaseModel] = RouteDistanceSchema
    city_map: networkx.classes.multidigraph.MultiDiGraph = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map: str, **kwargs):
        super().__init__(**kwargs)
        if not city_map:
            raise Exception('A valid city map path to a graphml file must be provided.')
        self.city_map = ox.load_graphml(city_map)
        self.city_map = ox.routing.add_edge_speeds(self.city_map)
        self.city_map = ox.routing.add_edge_travel_times(self.city_map)
    
    def _run(self, *args, **kwargs) -> int:
        args = args[0]
        x_origin = args.get('x_origin')
        y_origin = args.get('y_origin')
        x_destination = args.get('x_destination')
        y_destination = args.get('y_destination')
        
        return self._find_distance(x_origin, y_origin, x_destination, y_destination)

    def _find_distance(self, x_origin: float, y_origin: float, x_destination: float, y_destination: float) -> int:
        origin_node = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
        destination_node = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)
        route = ox.shortest_path(self.city_map, origin_node, destination_node, weight='travel_time')
        edge_lengths = ox.routing.route_to_gdf(self.city_map, route)['length']

        return round(sum(edge_lengths))