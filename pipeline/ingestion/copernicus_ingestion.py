"""
Copernicus Marine Satellite Data Ingestion Entry Point & Re-export
------------------------------------------------------------------
Re-exports CopernicusIngestor and CLI tools from copernicus_ingestor.py
for convenient imports and compatibility.
"""

from transformers import Optional

from pipeline.ingestion.copernicus_ingestor import (
    CopernicusIngestor,
    run_ingestor_cli,
    main,
)

mock_mode: bool = False,
db_writer:  Optional[DBWriter] = None,

from pipeline.storage.db_writer import DBWriter

__all__ = ["CopernicusIngestor", "run_ingestor_cli", "main"]

if __name__ == "__main__":
    main()
