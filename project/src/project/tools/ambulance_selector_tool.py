import networkx
import json
import osmnx as ox
from crewai_tools import BaseTool
from typing import List, Dict, Optional, Type, Any
from pydantic import BaseModel, Field

class AmbulanceSelectorSchema(BaseModel):
    """Input schema for the Ambulance Selector Tool."""
    fire_location: str = Field(..., description='Address of the fire emergency.')
    ambulances_needed: int = Field(..., description='Number of ambulances required.')

class AmbulanceSelectorTool(BaseTool):
    name: str = 'Ambulance Selector Tool'
    description: str = 'This tool selects the N closest ambulances to the fire location.'
    args_schema: Type[BaseModel] = AmbulanceSelectorSchema
    city_map: networkx.classes.multidigraph.MultiDiGraph = None
    ambulances: dict = List[Dict]
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map: str, input, **kwargs):
        super().__init__(**kwargs)

        # Initialize the map
        self.city_map = ox.load_graphml(city_map)
        self.city_map = ox.routing.add_edge_speeds(self.city_map)
        self.city_map = ox.routing.add_edge_travel_times(self.city_map)

        self.ambulances = input
    
    def _run(self, fire_location: str, ambulances_needed: int) -> List[Dict[str, Any]]:
        # Geocode the fire location
        try:
            fire_coordinates = ox.geocode(fire_location)
        except Exception as e:
            raise ValueError(f"Error geocoding fire location: {e}")
        x_fire, y_fire = fire_coordinates[1], fire_coordinates[0]

        # List to store distances for each ambulance
        ambulance_distances = []

        # Loop over each ambulance and calculate distance
        for amb_id, amb_location in self.ambulances.items():
            try:
                # Geocode ambulance location
                amb_coordinates = ox.geocode(amb_location)
            except Exception as e:
                print(f"Error geocoding ambulance {amb_id} at {amb_location}: {e}")
                continue  # Skip this ambulance if geocoding fails
            
            x_amb, y_amb = amb_coordinates[1], amb_coordinates[0]
            try:
                # Calculate distance from fire to ambulance
                distance = self._find_distance(x_fire, y_fire, x_amb, y_amb)
            except Exception as e:
                print(f"Error calculating distance for ambulance {amb_id}: {e}")
                continue

            ambulance_distances.append({
                "ambulance_id": amb_id,
                "distance": distance,
                "location": amb_location
            })

        # Sort ambulances by distance (ascending order)
        ambulance_distances.sort(key=lambda x: x["distance"])

        # Select the required number of closest ambulances
        selected_ambulances = ambulance_distances[:ambulances_needed]

        print('Ambulances results:')
        print(ambulance_distances)

        return selected_ambulances


    def _find_distance(self, x_origin: float, y_origin: float, x_destination: float, y_destination: float) -> int:
        origin_node = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
        destination_node = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)
        route = ox.shortest_path(self.city_map, origin_node, destination_node, weight='travel_time')
        edge_lengths = ox.routing.route_to_gdf(self.city_map, route)['length']

        return round(sum(edge_lengths))