import math
from typing import Tuple

def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two points on earth in kilometers."""
    R = 6371.0 # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def calculate_nautical_miles(km: float) -> float:
    """Converts kilometers to nautical miles."""
    return round(km * 0.539957, 2)

def calculate_bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, str]:
    """Calculates forward azimuth bearing in degrees and cardinal direction."""
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
         math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1)))
    initial_bearing = math.degrees(math.atan2(y, x))
    compass_bearing = (initial_bearing + 360) % 360

    cardinals = ["NORTH", "NORTH-EAST", "EAST", "SOUTH-EAST", "SOUTH", "SOUTH-WEST", "WEST", "NORTH-WEST"]
    idx = int((compass_bearing + 22.5) / 45) % 8
    return round(compass_bearing, 1), cardinals[idx]
