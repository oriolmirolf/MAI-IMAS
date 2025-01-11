import networkx as nx
import osmnx as ox
from crewai.tools import BaseTool
from typing import Type, Dict, Any
from pydantic import BaseModel, Field

class FireCrewNavigatorSchema(BaseModel):
    """Input schema for the Fire Crew Navigator Tool."""
    fire_location: str = Field(..., description='Address of the fire emergency.')

class FireCrewNavigatorTool(BaseTool):
    name: str = 'Fire Crew Navigator Tool'
    description: str = 'Computes the optimal route and distance from the fire station to the fire location.'
    args_schema: Type[BaseModel] = FireCrewNavigatorSchema
    city_map: nx.MultiDiGraph = None
    fire_station_location: str = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map_file: str, fire_station_location: str, **kwargs):
        super().__init__(**kwargs)

        # Initialize the map
        self.city_map = ox.load_graphml(city_map_file)
        self.city_map = ox.add_edge_speeds(self.city_map)
        self.city_map = ox.add_edge_travel_times(self.city_map)

        # Set the fire station location
        self.fire_station_location = fire_station_location

    def _run(self, fire_location: str) -> Dict[str, Any]:
        
        fire_location = "Carrer de la Unió, 8-24, 08800 Vilanova i la Geltrú, Barcelona"
        # Geocode the fire location
        try:
            fire_coordinates = ox.geocode(fire_location)
        except Exception as e:
            raise ValueError(f"Error geocoding fire location: {e}")
        y_fire, x_fire = fire_coordinates[0], fire_coordinates[1]

        # Geocode the fire station location
        try:
            station_coordinates = ox.geocode(self.fire_station_location)
        except Exception as e:
            raise ValueError(f"Error geocoding fire station location: {e}")
        y_station, x_station = station_coordinates[0], station_coordinates[1]

        try:
            # Compute the route and related information
            route_info = self._compute_route(x_station, y_station, x_fire, y_fire)
        except Exception as e:
            raise ValueError(f"Error computing route: {e}")

        return route_info

    def _compute_route(self, x_origin: float, y_origin: float, x_destination: float, y_destination: float) -> Dict[str, Any]:
        # Find the nearest nodes to the origin and destination
        origin_node = ox.nearest_nodes(self.city_map, x_origin, y_origin)
        destination_node = ox.nearest_nodes(self.city_map, x_destination, y_destination)

        # Compute the shortest path based on travel time
        route = nx.shortest_path(self.city_map, origin_node, destination_node, weight='travel_time')

        # Get edge attributes for the route
        route_edges = ox.utils_graph.get_route_edge_attributes(self.city_map, route)

        # Calculate total length and travel time
        total_length = sum(edge['length'] for edge in route_edges)  # in meters
        total_travel_time = sum(edge['travel_time'] for edge in route_edges)  # in seconds

        # Extract route coordinates
        route_coords = []
        for node in route:
            x = self.city_map.nodes[node]['x']
            y = self.city_map.nodes[node]['y']
            route_coords.append({'x': x, 'y': y})

        return {
            'route_coordinates': route_coords,
            'total_length_meters': round(total_length, 2),
            'total_travel_time_minutes': round(total_travel_time / 60, 2)  # Convert seconds to minutes
        }
