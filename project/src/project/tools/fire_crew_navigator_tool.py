import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field

class FireCrewNavigatorSchema(BaseModel):
    """Input schema for the Fire Crew Navigator Tool."""
    fire_location: str = Field(..., description='Address of the fire emergency.')

class FireCrewNavigatorTool(BaseTool):
    name: str = 'Fire Crew Navigator Tool'
    description: str = 'Computes the optimal route and distance from the fire station to the fire location.'
    args_schema: Type[BaseModel] = FireCrewNavigatorSchema
    city_map: nx.classes.multidigraph.MultiDiGraph = None
    fire_station_location: str = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map_file: str, fire_station_location: str, **kwargs):
        super().__init__(**kwargs)

        # Initialize the map
        self.city_map = ox.load_graphml(city_map_file)
        self.city_map = ox.routing.add_edge_speeds(self.city_map)
        self.city_map = ox.routing.add_edge_travel_times(self.city_map)

        # Set the fire station location
        self.fire_station_location = fire_station_location
    
    
    def compute_route(self, origin_location: str, destination_location: str) -> List[str]:
        try:
            origin_coordinates = ox.geocode(origin_location)
            destination_coordinates = ox.geocode(destination_location)

            x_origin, y_origin = origin_coordinates[1], origin_coordinates[0]
            x_destination, y_destination = destination_coordinates[1], destination_coordinates[0]

            origin = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
            destination = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)

            route = ox.shortest_path(self.city_map, origin, destination, weight='travel_time')
            fig, ax = ox.plot_graph_route(self.city_map, route, node_size=0)
            plt.show()
            # fig.savefig('firefighter_route_map.png', dpi=300)

            
            route_gdf = ox.routing.route_to_gdf(self.city_map, route)
            route_gdf = route_gdf['name'].fillna('').reset_index(drop=True)

            route_directions = []
            for i, street_name in enumerate(route_gdf):
                if street_name != '' and (i == 0 or street_name != route_gdf[i - 1]):
                    direction = street_name
                    route_directions.append(direction)

            return route_directions

        
        except Exception as e:
            raise ValueError(f"Error geocoding location: {e}")
        

    def _run(self, fire_location: str) -> Dict[str, dict]:
        return self.compute_route(self.fire_station_location, fire_location)
