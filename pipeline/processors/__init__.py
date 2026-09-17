"""
ORCA Pipeline Processors Package
--------------------------------
Provides scientific data processors for Earth Observation (EO) satellite rasters,
including NetCDF (Copernicus Marine) and GeoTIFF (NASA GEE MODIS) formats,
converting raw rasters into lightweight GeoJSON tiles for client map rendering.
"""

from pipeline.processors.netcdf_processor import NetCDFProcessor
from pipeline.processors.geotiff_processor import GeoTIFFProcessor

__all__ = ["NetCDFProcessor", "GeoTIFFProcessor"]
