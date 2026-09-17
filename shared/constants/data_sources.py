"""
Central configuration of external marine intelligence data sources.
"""

OPEN_METEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

INCOIS_METADATA_SOURCE = "INCOIS Oceansat-3 OCM-3 & INSAT-3DR Thermal Lineage"
EEZ_BOUNDARY_GEOJSON = "india_eez_boundaries.geojson"
MPA_BOUNDARY_GEOJSON = "india_marine_protected_areas.geojson"
SECTOR_BOUNDARY_GEOJSON = "india_coastal_fishing_sectors.geojson"

COASTAL_SECTORS_DATA = [
    {"id": "kochi", "name": "Kochi Sector K-04", "lat": 9.9312, "lng": 75.8234, "state": "Kerala"},
    {"id": "munambam", "name": "Munambam Sector M-02", "lat": 10.20, "lng": 75.80, "state": "Kerala"},
    {"id": "alappuzha", "name": "Alappuzha Shoals A-09", "lat": 9.45, "lng": 76.15, "state": "Kerala"},
    {"id": "goa", "name": "Goa Coastal Zone G-08", "lat": 15.35, "lng": 73.55, "state": "Goa"},
    {"id": "mumbai", "name": "Mumbai High Corridor B-12", "lat": 18.90, "lng": 72.40, "state": "Maharashtra"},
    {"id": "mangalore", "name": "Mangalore Deep MN-03", "lat": 12.82, "lng": 74.52, "state": "Karnataka"},
    {"id": "chennai", "name": "Chennai Coromandel C-03", "lat": 13.10, "lng": 80.45, "state": "Tamil Nadu"},
    {"id": "rameswaram", "name": "Palk Strait R-01", "lat": 9.25, "lng": 79.35, "state": "Tamil Nadu"},
    {"id": "vizag", "name": "Visakhapatnam Shelf V-06", "lat": 17.65, "lng": 83.42, "state": "Andhra Pradesh"},
    {"id": "paradip", "name": "Paradip Coastal Sector P-02", "lat": 20.20, "lng": 86.68, "state": "Odisha"},
    {"id": "sundarbans", "name": "Sundarbans Sector SB-01", "lat": 21.50, "lng": 88.50, "state": "West Bengal"}
]
