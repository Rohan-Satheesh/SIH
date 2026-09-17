"""
Pipeline Ingestion Package
--------------------------
Handles automated data acquisition from remote providers (Copernicus Marine, etc.).
"""

def __getattr__(name: str):
    if name == "CopernicusIngestor":
        from .copernicus_ingestor import CopernicusIngestor
        return CopernicusIngestor
    if name == "NasaGeeIngestor":
        from .nasa_gee_ingestor import NasaGeeIngestor
        return NasaGeeIngestor
    if name == "NoaaIngestor":
        from .noaa_ingestor import NoaaIngestor
        return NoaaIngestor
    if name == "IncoisScraper":
        from .incois_scraper import IncoisScraper
        return IncoisScraper
    if name == "ImdScraper":
        from .imd_scraper import ImdScraper
        return ImdScraper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["CopernicusIngestor", "NasaGeeIngestor", "NoaaIngestor", "IncoisScraper", "ImdScraper"]


