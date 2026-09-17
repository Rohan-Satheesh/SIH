"""
Vector Spatial Indexer & RAG Advisory Vector Store Module (CHUNK_ID: R4-C07 & R4-C10)
-------------------------------------------------------------------------------------
Role: Role 4 (Data Pipeline Engineer)
Target: pipeline/storage/vector_indexer.py
Prerequisites: [R4-C05], [R4-C06], [R4-C07]

Components:
1. VectorIndexer (R4-C07):
   Lightweight spatial grid indexer for processed vector GeoJSON datasets
   generated from NetCDF/GeoTIFF satellite rasters.

2. AdvisoryVectorIndexer (R4-C10):
   RAG Advisory Vector Store Indexer using ChromaDB and Sentence-Transformers
   (sentence-transformers/all-MiniLM-L6-v2).
   Chunks INCOIS PFZ/OSF advisories, IMD coastal/marine warning bulletins,
   and marine safety guidelines using RecursiveCharacterTextSplitter
   (chunk_size=500, overlap=50).
   Maintains citation metadata (source, date, source_url, document ID, sector info)
   with idempotent upsert via deterministic chunk IDs.
"""

import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timezone

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import ChromaConfig

logger = logging.getLogger("vector_indexer")

# -----------------------------------------------------------------------------
# Optional Imports for Vector Store (CHUNK_ID: R4-C10)
# -----------------------------------------------------------------------------
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except (ImportError, OSError) as exc:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("Sentence Transformers unavailable: %s", exc)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    HAS_TEXT_SPLITTER = True
except ImportError:
    HAS_TEXT_SPLITTER = False


# =============================================================================
# PART 1: Spatial Grid Indexer for GeoJSON (CHUNK_ID: R4-C07) - PRESERVED
# =============================================================================

class VectorIndexer:
    """
    Lightweight spatial indexer for vector GeoJSON feature collections.
    Builds a spatial grid index across geographic coordinates (lon, lat)
    to allow sub-millisecond bounding box and nearest-neighbor queries.
    """

    def __init__(self, grid_size: float = 1.0):
        """
        Initialize the spatial indexer.

        Args:
            grid_size: Cell size in degrees for the spatial bucket hash (default 1.0 degree).
        """
        self.grid_size = grid_size
        self.buckets: Dict[Tuple[int, int], List[int]] = {}
        self.features: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.bounds: Optional[Tuple[float, float, float, float]] = None

    def _get_bucket_key(self, lon: float, lat: float) -> Tuple[int, int]:
        """Convert float lon/lat into discrete spatial bucket coordinate."""
        return int(lon // self.grid_size), int(lat // self.grid_size)

    def index_geojson(self, geojson_data: Union[Dict[str, Any], str, Path]) -> int:
        """
        Index a GeoJSON FeatureCollection dictionary, JSON string, or file path.

        Returns:
            Number of indexed features.
        """
        if isinstance(geojson_data, (str, Path)):
            path = Path(geojson_data)
            if path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(str(geojson_data))
        else:
            data = geojson_data

        self.metadata = data.get("metadata", {})
        features = data.get("features", [])
        self.features = features
        self.buckets.clear()

        min_lon = float("inf")
        min_lat = float("inf")
        max_lon = float("-inf")
        max_lat = float("-inf")

        for idx, feat in enumerate(features):
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            geom_type = geom.get("type", "")

            if geom_type == "Point" and len(coords) >= 2:
                lon, lat = float(coords[0]), float(coords[1])
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)

                b_key = self._get_bucket_key(lon, lat)
                self.buckets.setdefault(b_key, []).append(idx)

            elif geom_type == "Polygon" and coords:
                ring = coords[0]
                if ring:
                    poly_lons = [p[0] for p in ring]
                    poly_lats = [p[1] for p in ring]
                    c_lon = sum(poly_lons) / len(poly_lons)
                    c_lat = sum(poly_lats) / len(poly_lats)

                    min_lon = min(min_lon, min(poly_lons))
                    max_lon = max(max_lon, max(poly_lons))
                    min_lat = min(min_lat, min(poly_lats))
                    max_lat = max(max_lat, max(poly_lats))

                    b_key = self._get_bucket_key(c_lon, c_lat)
                    self.buckets.setdefault(b_key, []).append(idx)

        if self.features:
            self.bounds = (min_lon, min_lat, max_lon, max_lat)
        logger.info(f"Indexed {len(features)} features across {len(self.buckets)} spatial buckets.")
        return len(features)

    def query_bbox(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float
    ) -> List[Dict[str, Any]]:
        """
        Query all features strictly within the given bounding box [min_lon, min_lat, max_lon, max_lat].
        """
        b_min_x = int(min_lon // self.grid_size)
        b_max_x = int(max_lon // self.grid_size)
        b_min_y = int(min_lat // self.grid_size)
        b_max_y = int(max_lat // self.grid_size)

        candidate_indices = set()
        for bx in range(b_min_x, b_max_x + 1):
            for by in range(b_min_y, b_max_y + 1):
                indices = self.buckets.get((bx, by), [])
                candidate_indices.update(indices)

        results = []
        for idx in candidate_indices:
            feat = self.features[idx]
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            geom_type = geom.get("type", "")

            if geom_type == "Point" and len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                    results.append(feat)
            else:
                results.append(feat)

        return results

    def query_nearest(
        self,
        lon: float,
        lat: float,
        k: int = 1,
        max_distance_deg: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Find k nearest vector features to a given geographic point (lon, lat)."""
        search_radius = max(self.grid_size, max_distance_deg)
        candidates = self.query_bbox(
            lon - search_radius,
            lat - search_radius,
            lon + search_radius,
            lat + search_radius
        )

        if not candidates:
            return []

        def dist_sq(f):
            c = f["geometry"]["coordinates"]
            return (c[0] - lon) ** 2 + (c[1] - lat) ** 2

        candidates.sort(key=dist_sq)
        return candidates[:k]

    def get_summary(self) -> Dict[str, Any]:
        """Return summary of the indexed dataset."""
        return {
            "total_features": len(self.features),
            "total_buckets": len(self.buckets),
            "bounds": self.bounds,
            "grid_size_deg": self.grid_size,
            "metadata": self.metadata
        }


# =============================================================================
# PART 2: RAG Advisory Vector Store Indexer (CHUNK_ID: R4-C10)
# =============================================================================

class AdvisoryVectorIndexer:
    """
    RAG Advisory Vector Store Indexer for marine advisories, warnings, and guidelines.
    Uses ChromaDB for local persistent vector storage and sentence-transformers
    (all-MiniLM-L6-v2) for semantic dense embeddings.
    """

    DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_COLLECTION_NAME = "marine_advisories"
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    def __init__(
        self,
        persist_directory: Optional[Union[str, Path]] = None,
        collection_name: Optional[str] = None,
        model_name: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        """
        Initialize the Advisory Vector Indexer.

        Args:
            persist_directory: Path to local persistent ChromaDB storage directory.
            collection_name: Name of the vector collection.
            model_name: Sentence-Transformers model name.
            chunk_size: RecursiveCharacterTextSplitter chunk size (characters).
            chunk_overlap: RecursiveCharacterTextSplitter chunk overlap (characters).
        """
        if not HAS_CHROMADB:
            raise ImportError(
                "ChromaDB is required for AdvisoryVectorIndexer. "
                "Install via 'pip install chromadb'."
            )
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers is required for AdvisoryVectorIndexer. "
                "Install via 'pip install sentence-transformers'."
            )
        if not HAS_TEXT_SPLITTER:
            raise ImportError(
                "langchain-text-splitters is required for AdvisoryVectorIndexer. "
                "Install via 'pip install langchain-text-splitters'."
            )

        self.persist_dir = Path(
            persist_directory or getattr(ChromaConfig, "PERSIST_DIR", ".chroma_db")
        )
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.collection_name = (
            collection_name or getattr(ChromaConfig, "COLLECTION_NAME", self.DEFAULT_COLLECTION_NAME)
        )
        self.model_name = (
            model_name or getattr(ChromaConfig, "EMBEDDING_MODEL", self.DEFAULT_MODEL_NAME)
        )
        self.chunk_size = chunk_size or getattr(ChromaConfig, "CHUNK_SIZE", self.DEFAULT_CHUNK_SIZE)
        self.chunk_overlap = chunk_overlap or getattr(ChromaConfig, "CHUNK_OVERLAP", self.DEFAULT_CHUNK_OVERLAP)

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # Initialize persistent Chroma client
        logger.info(f"Connecting to ChromaDB at '{self.persist_dir}'...")
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "NeerMitra Marine Advisories and Warnings Vector Store"}
        )

        # Lazy-loaded model instance
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazily load and return the SentenceTransformer embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def _generate_chunk_id(self, source: str, doc_id: str, chunk_index: int) -> str:
        """
        Generate a deterministic, stable ID for a chunk.
        Guarantees that repeated indexing runs perform idempotent upserts without duplicates.
        """
        raw_key = f"{source}:{doc_id}:{chunk_index}"
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]
        return f"{source}_{digest}_{chunk_index}"

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata dictionary for ChromaDB storage.
        ChromaDB only accepts str, int, float, or bool values in metadata.
        Converts lists, dicts, or None to string representations.
        """
        sanitized = {}
        for k, v in metadata.items():
            if v is None:
                sanitized[k] = ""
            elif isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            elif isinstance(v, (list, tuple)):
                sanitized[k] = ", ".join(str(item) for item in v) if v else ""
            elif isinstance(v, dict):
                sanitized[k] = json.dumps(v, ensure_ascii=False)
            else:
                sanitized[k] = str(v)
        return sanitized

    # -------------------------------------------------------------------------
    # Core Indexing Logic
    # -------------------------------------------------------------------------

    def index_text_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Split a text document into chunks, generate embeddings, and upsert into ChromaDB.

        Args:
            text: Raw document text to index.
            metadata: Citation metadata (source, date, source_url, advisory_type, etc.).
            doc_id: Unique identifier for the document. If omitted, generated from text hash.

        Returns:
            Dict containing chunks_created, ids_upserted, and doc_id.
        """
        clean_text = (text or "").strip()
        if not clean_text:
            logger.warning(f"Skipping empty text document (doc_id={doc_id}).")
            return {"status": "skipped", "reason": "empty_text", "chunks_created": 0}

        doc_identifier = doc_id or hashlib.sha256(clean_text.encode("utf-8")).hexdigest()[:16]
        source = str(metadata.get("source", "UNKNOWN"))

        # Chunk the text
        raw_chunks = self.text_splitter.split_text(clean_text)
        if not raw_chunks:
            return {"status": "skipped", "reason": "no_chunks_produced", "chunks_created": 0}

        chunk_ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for idx, chunk_text in enumerate(raw_chunks):
            c_text = chunk_text.strip()
            if not c_text:
                continue

            c_id = self._generate_chunk_id(source, doc_identifier, idx)
            c_meta = dict(metadata)
            c_meta["doc_id"] = doc_identifier
            c_meta["chunk_index"] = idx
            c_meta["total_chunks"] = len(raw_chunks)
            c_meta["indexed_at"] = datetime.now(timezone.utc).isoformat()

            chunk_ids.append(c_id)
            documents.append(c_text)
            metadatas.append(self._sanitize_metadata(c_meta))

        if not chunk_ids:
            return {"status": "skipped", "reason": "empty_chunks_after_strip", "chunks_created": 0}

        # Generate embeddings
        try:
            embeddings = self.model.encode(documents, show_progress_bar=False).tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed for doc {doc_identifier}: {e}")
            raise

        # Upsert into ChromaDB
        try:
            self.collection.upsert(
                ids=chunk_ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(
                f"[UPSERT] Indexed {len(chunk_ids)} chunks for doc '{doc_identifier}' "
                f"({source} - {metadata.get('advisory_type')})"
            )
            return {
                "status": "success",
                "doc_id": doc_identifier,
                "chunks_created": len(chunk_ids),
                "ids_upserted": chunk_ids,
            }
        except Exception as e:
            logger.error(f"ChromaDB upsert failed for doc {doc_identifier}: {e}")
            raise

    # -------------------------------------------------------------------------
    # Specialized Parsers for Real Pipeline Outputs
    # -------------------------------------------------------------------------

    def index_incois_advisory(self, data_or_path: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """
        Parse and index a normalized INCOIS JSON advisory file (PFZ or OSF).
        """
        if isinstance(data_or_path, (str, Path)):
            p = Path(data_or_path)
            if not p.is_file():
                raise FileNotFoundError(f"INCOIS file not found: {p}")
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = data_or_path

        advisory_type = data.get("advisory_type", "incois")
        date_str = data.get("date", datetime.now(timezone.utc).date().isoformat())
        source = "INCOIS"
        source_urls = data.get("source_urls", [])
        primary_url = source_urls[0] if source_urls else "https://incois.gov.in"
        alert_level = data.get("alert_level", "none")

        results = []

        # 1. Main advisory text
        main_text = data.get("advisory_text", "").strip()
        if main_text:
            meta = {
                "source": source,
                "advisory_type": advisory_type,
                "date": date_str,
                "source_url": primary_url,
                "alert_level": alert_level,
                "section": "main_advisory_text",
            }
            res = self.index_text_document(
                text=main_text,
                metadata=meta,
                doc_id=f"incois_{advisory_type}_{date_str}_main"
            )
            results.append(res)

        # 2. Raw bulletins if attached
        for b_idx, b in enumerate(data.get("raw_bulletins", [])):
            b_text = b.get("text", "").strip()
            if b_text and b_text != main_text:
                b_url = b.get("source_url", primary_url)
                b_title = b.get("title", "Bulletin")
                b_id = hashlib.sha256(b_url.encode()).hexdigest()[:8]
                meta = {
                    "source": source,
                    "advisory_type": advisory_type,
                    "date": date_str,
                    "source_url": b_url,
                    "title": b_title,
                    "alert_level": alert_level,
                    "section": f"bulletin_{b_idx}",
                }
                res = self.index_text_document(
                    text=b_text,
                    metadata=meta,
                    doc_id=f"incois_{advisory_type}_{date_str}_bulletin_{b_id}"
                )
                results.append(res)

        total_chunks = sum(r.get("chunks_created", 0) for r in results)
        return {
            "source": source,
            "advisory_type": advisory_type,
            "date": date_str,
            "sections_indexed": len(results),
            "total_chunks": total_chunks,
            "details": results
        }

    def index_imd_warnings(self, data_or_path: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """
        Parse and index normalized IMD marine warnings & CAP alerts JSON.
        """
        if isinstance(data_or_path, (str, Path)):
            p = Path(data_or_path)
            if not p.is_file():
                raise FileNotFoundError(f"IMD file not found: {p}")
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = data_or_path

        date_str = data.get("date", datetime.now(timezone.utc).date().isoformat())
        source = "IMD"
        overall_severity = data.get("overall_severity", "none")
        results = []

        # 1. Warning categories (coastal weather, fishermen, sea area, port)
        for warn in data.get("warnings", []):
            name = warn.get("name", "marine_warning")
            label = warn.get("label", name)
            source_url = warn.get("source_url", "https://rsmcnewdelhi.imd.gov.in")
            severity = warn.get("severity", overall_severity)
            areas = warn.get("affected_areas", [])

            # Check combined text or bulletins
            preview_text = warn.get("combined_text_preview", "").strip()
            bulletins = warn.get("bulletins", [])

            if preview_text:
                meta = {
                    "source": source,
                    "advisory_type": "imd_warning",
                    "sub_type": name,
                    "date": date_str,
                    "source_url": source_url,
                    "title": label,
                    "severity": severity,
                    "geographic_info": areas,
                }
                res = self.index_text_document(
                    text=preview_text,
                    metadata=meta,
                    doc_id=f"imd_{name}_{date_str}"
                )
                results.append(res)
            elif bulletins:
                for b_idx, b in enumerate(bulletins):
                    b_text = b.get("text", "").strip()
                    if b_text:
                        b_url = b.get("source_url", source_url)
                        meta = {
                            "source": source,
                            "advisory_type": "imd_warning",
                            "sub_type": name,
                            "date": date_str,
                            "source_url": b_url,
                            "title": b.get("title", label),
                            "severity": severity,
                            "geographic_info": areas,
                        }
                        res = self.index_text_document(
                            text=b_text,
                            metadata=meta,
                            doc_id=f"imd_{name}_{date_str}_bulletin_{b_idx}"
                        )
                        results.append(res)

        # 2. CAP alerts
        for c_idx, cap in enumerate(data.get("cap_alerts", [])):
            headline = cap.get("headline") or cap.get("title") or ""
            desc = cap.get("description") or ""
            instruction = cap.get("instruction") or ""
            cap_text = f"{headline}\n\n{desc}\n\n{instruction}".strip()

            if cap_text:
                cap_id = cap.get("id") or f"cap_{c_idx}"
                meta = {
                    "source": source,
                    "advisory_type": "cap_alert",
                    "date": date_str,
                    "source_url": cap.get("link") or "https://cap-sources.s3.amazonaws.com",
                    "title": headline or "CAP Marine Alert",
                    "severity": cap.get("severity") or overall_severity,
                    "geographic_info": cap.get("area_desc") or cap.get("event") or "",
                }
                res = self.index_text_document(
                    text=cap_text,
                    metadata=meta,
                    doc_id=f"imd_cap_{date_str}_{cap_id}"
                )
                results.append(res)

        total_chunks = sum(r.get("chunks_created", 0) for r in results)
        return {
            "source": source,
            "date": date_str,
            "sections_indexed": len(results),
            "total_chunks": total_chunks,
            "details": results
        }

    def index_directory(self, dir_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Scan a directory and index all detected INCOIS / IMD advisory JSON files.
        """
        p = Path(dir_path)
        if not p.is_dir():
            raise NotADirectoryError(f"Directory not found: {p}")

        incois_files = list(p.glob("pfz_*.json")) + list(p.glob("osf_*.json"))
        imd_files = list(p.glob("imd_*.json"))
        guideline_files = list(p.glob("*.txt")) + list(p.glob("guideline_*.json"))

        indexed_summary = {
            "directory": str(p),
            "incois_files_found": len(incois_files),
            "imd_files_found": len(imd_files),
            "guideline_files_found": len(guideline_files),
            "total_chunks_indexed": 0,
            "file_summaries": []
        }

        # Index INCOIS
        for f in incois_files:
            try:
                res = self.index_incois_advisory(f)
                indexed_summary["total_chunks_indexed"] += res.get("total_chunks", 0)
                indexed_summary["file_summaries"].append({"file": f.name, "result": res})
            except Exception as e:
                logger.error(f"Failed to index INCOIS file {f.name}: {e}")
                indexed_summary["file_summaries"].append({"file": f.name, "error": str(e)})

        # Index IMD
        for f in imd_files:
            try:
                res = self.index_imd_warnings(f)
                indexed_summary["total_chunks_indexed"] += res.get("total_chunks", 0)
                indexed_summary["file_summaries"].append({"file": f.name, "result": res})
            except Exception as e:
                logger.error(f"Failed to index IMD file {f.name}: {e}")
                indexed_summary["file_summaries"].append({"file": f.name, "error": str(e)})

        # Index text guidelines
        for f in guideline_files:
            try:
                text = f.read_text(encoding="utf-8")
                res = self.index_text_document(
                    text=text,
                    metadata={"source": "GUIDELINE", "advisory_type": "marine_guideline", "title": f.stem},
                    doc_id=f"guide_{f.stem}"
                )
                indexed_summary["total_chunks_indexed"] += res.get("chunks_created", 0)
                indexed_summary["file_summaries"].append({"file": f.name, "result": res})
            except Exception as e:
                logger.error(f"Failed to index guideline file {f.name}: {e}")
                indexed_summary["file_summaries"].append({"file": f.name, "error": str(e)})

        return indexed_summary

    # -------------------------------------------------------------------------
    # Retrieval & Querying (For RAG / AI Copilot)
    # -------------------------------------------------------------------------

    def query_advisories(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for semantic matches to an advisory query.

        Args:
            query_text: Natural language query (e.g. "cyclone alert Odisha coast").
            n_results: Number of nearest matches to return.
            where: Optional ChromaDB metadata filter dict.

        Returns:
            List of result dicts with chunk text, score/distance, and citation metadata.
        """
        clean_query = query_text.strip()
        if not clean_query:
            return []

        # Generate query embedding
        query_emb = self.model.encode([clean_query], show_progress_bar=False).tolist()

        kwargs: Dict[str, Any] = {
            "query_embeddings": query_emb,
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        raw_res = self.collection.query(**kwargs)

        formatted = []
        docs = raw_res.get("documents", [[]])[0]
        metas = raw_res.get("metadatas", [[]])[0]
        distances = raw_res.get("distances", [[]])[0]
        ids = raw_res.get("ids", [[]])[0]

        for i in range(len(docs)):
            formatted.append({
                "id": ids[i],
                "document": docs[i],
                "metadata": metas[i] if i < len(metas) else {},
                "distance": distances[i] if i < len(distances) else None,
                # Citation convenience fields
                "citation": {
                    "source": metas[i].get("source") if i < len(metas) else "UNKNOWN",
                    "date": metas[i].get("date") if i < len(metas) else "",
                    "source_url": metas[i].get("source_url") if i < len(metas) else "",
                    "title": metas[i].get("title") if i < len(metas) else "",
                    "geographic_info": metas[i].get("geographic_info") if i < len(metas) else "",
                    "alert_level": metas[i].get("alert_level") or metas[i].get("severity") if i < len(metas) else ""
                }
            })

        return formatted

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return count and storage metadata for the vector store."""
        return {
            "collection_name": self.collection_name,
            "persist_directory": str(self.persist_dir),
            "total_records": self.collection.count(),
            "embedding_model": self.model_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }


# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------

def run_cli():
    """Command line interface for vector indexer."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="NeerMitra RAG Advisory Vector Store Indexer (CHUNK_ID: R4-C10)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print vector store collection statistics"
    )
    parser.add_argument(
        "--index-dir",
        type=str,
        help="Directory containing INCOIS / IMD JSON advisories to index"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query the advisory vector store for semantic matches"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results to retrieve (default: 3)"
    )

    args = parser.parse_args()

    indexer = AdvisoryVectorIndexer()

    if args.status:
        stats = indexer.get_collection_stats()
        print("=" * 75)
        print("NeerMitra Advisory Vector Store Stats (CHUNK_ID: R4-C10)")
        print("=" * 75)
        for k, v in stats.items():
            print(f"  {k:<20}: {v}")
        print("=" * 75)
        return

    if args.index_dir:
        print(f"Indexing directory: {args.index_dir}...")
        summary = indexer.index_directory(args.index_dir)
        print(json.dumps(summary, indent=2))
        return

    if args.query:
        print(f"Executing semantic query: '{args.query}' (top {args.top_k})...\n")
        results = indexer.query_advisories(args.query, n_results=args.top_k)
        for idx, r in enumerate(results, 1):
            dist_str = f"{r['distance']:.4f}" if r['distance'] is not None else "N/A"
            snippet = r['document'][:200].replace("\n", " ")
            print(f"[{idx}] Match (distance: {dist_str}):")
            print(f"    Source:  {r['citation']['source']} | Date: {r['citation']['date']}")
            print(f"    URL:     {r['citation']['source_url']}")
            print(f"    Snippet: {snippet}...")
            print("-" * 60)
        return

    parser.print_help()


def main():
    run_cli()


if __name__ == "__main__":
    main()
