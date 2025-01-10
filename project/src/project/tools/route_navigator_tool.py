import networkx
import osmnx as ox
from crewai_tools import BaseTool
from typing import List, Dict, Type, Any
from pydantic import BaseModel, Field

class RouteNavigatorSchema(BaseModel):
    """Input schema for the Route Navigator Tool."""
    fire_location: str = Field(..., description='Address of the fire location.')
    ambulance_information: Dict = Field(..., description="""Dictionary containing as key the ambulance ids and as values another Dictionary with keys 'address1'
                                        and 'address2' containing the origin ambulance location address and the destination address, respectively.
                                        E.g: {"ambulance1": {"address1": "Origin location", "address2": "Destination location"},
                                              "ambulance2": {"address1": "Origin location", "address2": "Destination location"}, ...}""")

class RouteNavigatorTool(BaseTool):
    name: str = 'Route Navigator Tool'
    description: str = 'This tool returns a route between two locations, as a list of street names.'
    args_schema: Type[BaseModel] = RouteNavigatorSchema
    city_map: networkx.classes.multidigraph.MultiDiGraph = None
    route: list = List[str]
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map: str, **kwargs):
        super().__init__(**kwargs)

        self.city_map = ox.load_graphml(city_map)
        self.city_map = ox.routing.add_edge_speeds(self.city_map)
        self.city_map = ox.routing.add_edge_travel_times(self.city_map)

    def compute_route(self, origin_location: str, destination_location: str) -> List[str]:
        # Geocode the fire location
        try:
            origin_coordinates = ox.geocode(origin_location)
            destination_coordinates = ox.geocode(destination_location)

            x_origin, y_origin = origin_coordinates[1], origin_coordinates[0]
            x_destination, y_destination = destination_coordinates[1], destination_coordinates[0]

            origin = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
            destination = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)

            route = ox.shortest_path(self.city_map, origin, destination, weight='travel_time')
            #fig, ax = ox.plot_graph_route(self.city_map, route, node_size=0)
            #fig.savefig('route_map.png', dpi=300)
            
            route_df = ox.routing.route_to_gdf(self.city_map, route)
            route_df = route_df['name'].fillna('').reset_index(drop=True)
            route_list = []
            route_list = [street_name for i, street_name in enumerate(route_df) 
                        if street_name != '' and (i == 0 or street_name != route_df[i - 1])]
            
            route_list = [item for sublist in route_list for item in (sublist if isinstance(sublist, list) else [sublist])]

            return route_list
        
        except Exception as e:
            raise ValueError(f"Error geocoding location: {e}")

    
    def _run(self, fire_location: str, ambulance_information: dict) -> Dict[str, dict]:
        routes = {}
        for key, value in ambulance_information.items():
            routes[key] = {
                'route1': self.compute_route(value["address1"], fire_location),
                'route2': self.compute_route(fire_location, value["address2"])
            }

        return routes


    def _find_distance(self, x_origin: float, y_origin: float, x_destination: float, y_destination: float) -> int:
        origin_node = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
        destination_node = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)
        route = ox.shortest_path(self.city_map, origin_node, destination_node, weight='travel_time')
        edge_lengths = ox.routing.route_to_gdf(self.city_map, route)['length']

        return round(sum(edge_lengths))