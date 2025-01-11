import networkx
import osmnx as ox
from crewai.tools import BaseTool
from typing import List, Dict, Type, Any
from pydantic import BaseModel, Field

class HospitalSelectorSchema(BaseModel):
    """Input schema for the Hospital Selector Tool."""
    fire_location: str = Field(..., description='Address of the fire emergency.')
    normal_rooms_needed: int = Field(..., description='Number of Hospitalization rooms required.')
    ICU_rooms_needed: int = Field(..., description='Number of ICU rooms required.')

class HospitalSelectorTool(BaseTool):
    name: str = 'Hospital Selector Tool'
    description: str = 'This tool selects the closest available Hospitalizations and ICU rooms from the fire location.'
    args_schema: Type[BaseModel] = HospitalSelectorSchema
    city_map: networkx.classes.multidigraph.MultiDiGraph = None
    hospitals: Dict[str, str] = {}
    normal_rooms: Dict[str, str] = {}
    uci_rooms: Dict[str, str] = {}
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, city_map: str, input: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)

        # Initialize the map
        self.city_map = ox.load_graphml(city_map)
        self.city_map = ox.routing.add_edge_speeds(self.city_map)
        self.city_map = ox.routing.add_edge_travel_times(self.city_map)

        # Parse input data for hospitals and rooms
        self.hospitals = input.get("hospitals")
        self.normal_rooms = input.get("normal_rooms")
        self.uci_rooms = input.get("uci_rooms")
    
    def _run(self, fire_location: str, normal_rooms_needed: int, ICU_rooms_needed: int) -> List[Dict[str, Any]]:
        # Geocode the fire location
        try:
            fire_coordinates = ox.geocode(fire_location)
        except Exception as e:
            raise ValueError(f"Error geocoding fire location: {e}")
        x_fire, y_fire = fire_coordinates[1], fire_coordinates[0]

        # List to store information for each hospital
        hospital_info = []

        # Loop over each hospital to calculate distance and count available rooms
        for hosp_id, hosp_location in self.hospitals.items():
            try:
                # Geocode hospital location
                hosp_coordinates = ox.geocode(hosp_location)
            except Exception as e:
                print(f"Error geocoding hospital {hosp_id} at {hosp_location}: {e}")
                continue  # Skip this hospital if geocoding fails
            
            x_hosp, y_hosp = hosp_coordinates[1], hosp_coordinates[0]
            try:
                # Calculate distance from fire to hospital
                distance = self._find_distance(x_fire, y_fire, x_hosp, y_hosp)
            except Exception as e:
                print(f"Error calculating distance for hospital {hosp_id}: {e}")
                continue

            # Count available rooms for this hospital
            normal_count = sum(1 for room, hosp in self.normal_rooms.items() if hosp == hosp_id)
            uci_count = sum(1 for room, hosp in self.uci_rooms.items() if hosp == hosp_id)

            hospital_info.append({
                "hospital_id": hosp_id,
                "hospital_location": hosp_location,
                "distance": distance,
                "normal_rooms_available": normal_count,
                "normal_rooms_ids": [room for room, hosp in self.normal_rooms.items() if hosp == hosp_id],
                "icu_rooms_available": uci_count,
                "icu_rooms_ids": [room for room, hosp in self.uci_rooms.items() if hosp == hosp_id]
            })
            
            # Construct natural language descriptions for each hospital
            descriptions = []
            for info in hospital_info:
                description = (
                    f"Hospital {info['hospital_id']} is located at {info['hospital_location']} and is "
                    f"{info['distance']} meters away from the fire location.\n"
                    f"* It has {info['normal_rooms_available']} normal room(s) available"
                )
                if info['normal_rooms_ids']:
                    normal_ids = ", ".join(map(str, info['normal_rooms_ids']))
                    description += f" with room IDs: {normal_ids}.\n"
                else:
                    description += ".\n"

                description += f"* It has {info['icu_rooms_available']} ICU room(s) available"
                if info['icu_rooms_ids']:
                    icu_ids = ", ".join(map(str, info['icu_rooms_ids']))
                    description += f" with room IDs: {icu_ids}."
                else:
                    description += "."

                descriptions.append(description)

            # Combine all hospital descriptions into one final string
            final_info_string = "\n\n".join(descriptions)
            return final_info_string


    def _find_distance(self, x_origin: float, y_origin: float, x_destination: float, y_destination: float) -> int:
        origin_node = ox.distance.nearest_nodes(self.city_map, X=x_origin, Y=y_origin)
        destination_node = ox.distance.nearest_nodes(self.city_map, X=x_destination, Y=y_destination)
        if origin_node == destination_node:
            return 0
        route = ox.shortest_path(self.city_map, origin_node, destination_node, weight='travel_time')
        edge_lengths = ox.routing.route_to_gdf(self.city_map, route)['length']

        return round(sum(edge_lengths))