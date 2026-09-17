"""
Scientific GeoTIFF Raster Processor (CHUNK_ID: R4-C07)
-------------------------------------------------------
Role: Role 4 (Data Pipeline Engineer)
Target: pipeline/processors/geotiff_processor.py
Prerequisites: [R4-C02, R4-C03]

Reads raw NASA GEE MODIS GeoTIFF files (MODIS-Aqua SST and Chlorophyll-a),
extracts geospatial arrays, affine transforms, CRS, bounds, and nodata flags,
performs clean scientific spatial interpolation for missing cloud-cover gaps,
and converts high-resolution raster arrays into lightweight vector GeoJSON tiles
suitable for fast frontend map display and B2 storage.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
try:
    import rasterio
    from rasterio.transform import xy
    HAS_RASTERIO = True
except (ImportError, OSError) as exc:
    rasterio = None
    xy = None
    HAS_RASTERIO = False
    logging.getLogger("geotiff_processor").warning(
        "Rasterio unavailable: %s", exc
    )

# Try importing scipy for advanced spatial interpolation
try:
    from scipy.interpolate import griddata
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from pipeline.config import NasaGeeConfig, B2Config
from pipeline.storage.b2_uploader import B2StorageManager
from pipeline.storage.vector_indexer import VectorIndexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("geotiff_processor")


class GeoTIFFProcessor:
    """
    Processes scientific GeoTIFF satellite rasters from NASA GEE (MODIS-Aqua),
    extracts geospatial bands, performs cloud-gap interpolation, and generates
    lightweight vector GeoJSON tiles for client map rendering and B2 storage.
    """

    BAND_CONFIGS: Dict[str, Dict[str, Any]] = {
        "sst": {
            "candidate_names": ["sst", "modis_aqua_sst", "temperature"],
            "description": "MODIS-Aqua Sea Surface Temperature",
            "target_units": "°C",
            "valid_min": 15.0,
            "valid_max": 36.0,
            "default_nodata": -9999.0,
            "b2_tile_template": "processed/tiles/sst/nasa-modis/{date}.geojson",
        },
        "chlor_a": {
            "candidate_names": ["chlor_a", "chlorophyll", "modis_aqua_chlor_a"],
            "description": "MODIS-Aqua Chlorophyll-a Concentration",
            "target_units": "mg/m³",
            "valid_min": 0.01,
            "valid_max": 30.0,
            "default_nodata": -9999.0,
            "b2_tile_template": "processed/tiles/chlorophyll/nasa-modis/{date}.geojson",
        }
    }

    def __init__(
        self,
        b2_manager: Optional[B2StorageManager] = None,
        staging_dir: Optional[Path] = None,
        mock_mode: bool = False,
        default_grid_step: float = 0.25  # ~25km downsampled grid for lightweight map rendering
    ):
        """
        Initialize the GeoTIFF processor.

        Args:
            b2_manager: Backblaze B2 storage manager instance.
            staging_dir: Local staging directory for temporary downloads/outputs.
            mock_mode: Whether to run in local simulation mode.
            default_grid_step: Spatial downsampling resolution in degrees for GeoJSON generation.
        """
        self.mock_mode = mock_mode
        self.b2_manager = b2_manager or B2StorageManager(mock_mode=mock_mode)
        self.staging_dir = Path(staging_dir) if staging_dir else PROJECT_ROOT / "staging" / "processed"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.default_grid_step = default_grid_step

    def open_raster(self, file_path: Union[str, Path]):
        """
        Open a GeoTIFF raster file with rasterio.
        """
        if not HAS_RASTERIO:
            raise RuntimeError(
                "GeoTIFF processing is unavailable because Rasterio could not be loaded."
            )

        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"GeoTIFF file does not exist: {file_path}")

        logger.info(
            f"Opening GeoTIFF raster: {file_path} ({path.stat().st_size} bytes)"
        )

        return rasterio.open(str(path))
    def identify_band_type(self, path: Path, tags: Dict[str, Any], requested_type: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Identify the satellite variable type from filename or raster metadata tags.
        """
        if requested_type and requested_type in self.BAND_CONFIGS:
            return requested_type, self.BAND_CONFIGS[requested_type]
        if requested_type == "chlorophyll" and "chlor_a" in self.BAND_CONFIGS:
            return "chlor_a", self.BAND_CONFIGS["chlor_a"]

        filename = path.name.lower()
        if "chlor" in filename:
            return "chlor_a", self.BAND_CONFIGS["chlor_a"]
        elif "sst" in filename:
            return "sst", self.BAND_CONFIGS["sst"]

        # Default fallback
        logger.warning(f"Could not conclusively infer band type from {path.name}. Defaulting to sst.")
        return "sst", self.BAND_CONFIGS["sst"]

    def interpolate_cloud_gaps(
        self,
        data_2d: np.ndarray,
        lats_2d: np.ndarray,
        lons_2d: np.ndarray,
        valid_min: Optional[float] = None,
        valid_max: Optional[float] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Cleanly interpolate missing nodata / NaN pixels caused by cloud cover over ocean domains.
        Does not invent invalid scientific data and restricts values to valid physical ranges.
        """
        arr = np.copy(data_2d)
        is_nan = np.isnan(arr)
        total_nan = int(np.sum(is_nan))

        if total_nan == 0 or total_nan == arr.size:
            return arr, 0

        valid_mask = ~is_nan
        valid_count = int(np.sum(valid_mask))
        if valid_count < 10:
            logger.warning("Too few valid points for spatial interpolation.")
            return arr, 0

        points = np.column_stack((lons_2d[valid_mask], lats_2d[valid_mask]))
        values = arr[valid_mask]

        interpolated_count = 0

        if HAS_SCIPY:
            try:
                nan_points = np.column_stack((lons_2d[is_nan], lats_2d[is_nan]))
                interp_linear = griddata(points, values, nan_points, method="linear")
                interp_nearest = griddata(points, values, nan_points, method="nearest")
                filled = np.where(np.isnan(interp_linear), interp_nearest, interp_linear)

                if valid_min is not None:
                    filled = np.maximum(filled, valid_min)
                if valid_max is not None:
                    filled = np.minimum(filled, valid_max)

                arr[is_nan] = filled
                interpolated_count = len(filled)
                logger.info(f"Interpolated {interpolated_count} cloud/missing GeoTIFF pixels using scipy.")
            except Exception as e:
                logger.warning(f"Scipy interpolation error ({e}). Using numpy neighborhood fallback.")
                arr, interpolated_count = self._numpy_spatial_interpolation(arr, is_nan, valid_min, valid_max)
        else:
            arr, interpolated_count = self._numpy_spatial_interpolation(arr, is_nan, valid_min, valid_max)

        return arr, interpolated_count

    def _numpy_spatial_interpolation(
        self,
        arr: np.ndarray,
        is_nan: np.ndarray,
        valid_min: Optional[float],
        valid_max: Optional[float],
        passes: int = 2
    ) -> Tuple[np.ndarray, int]:
        """
        Robust numpy neighborhood averaging fallback.
        """
        res = np.copy(arr)
        rows, cols = res.shape
        filled = 0

        for _ in range(passes):
            new_nans = np.isnan(res)
            for r in range(rows):
                for c in range(cols):
                    if new_nans[r, c]:
                        r_min = max(0, r - 1)
                        r_max = min(rows, r + 2)
                        c_min = max(0, c - 1)
                        c_max = min(cols, c + 2)
                        neighbors = res[r_min:r_max, c_min:c_max]
                        valid_neighbors = neighbors[~np.isnan(neighbors)]
                        if len(valid_neighbors) >= 3:
                            val = float(np.mean(valid_neighbors))
                            if valid_min is not None:
                                val = max(val, valid_min)
                            if valid_max is not None:
                                val = min(val, valid_max)
                            res[r, c] = val
                            filled += 1
        return res, filled

    def convert_to_vector_geojson(
        self,
        data_2d: np.ndarray,
        lats_2d: np.ndarray,
        lons_2d: np.ndarray,
        var_name: str,
        config: Dict[str, Any],
        date_str: str,
        crs_str: str,
        is_interpolated: bool = False,
        grid_step: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Convert processed GeoTIFF raster into lightweight vector GeoJSON FeatureCollection.
        """
        step = grid_step or self.default_grid_step
        target_units = config.get("target_units", "")
        v_min = config.get("valid_min")
        v_max = config.get("valid_max")

        height, width = data_2d.shape

        # Calculate coordinate spans to determine downsampling stride
        lat_span = abs(float(lats_2d[0, 0] - lats_2d[-1, 0])) if height > 1 else 1.0
        lon_span = abs(float(lons_2d[0, -1] - lons_2d[0, 0])) if width > 1 else 1.0

        lat_res = lat_span / max(height, 1)
        lon_res = lon_span / max(width, 1)

        row_stride = max(1, int(round(step / max(lat_res, 1e-6))))
        col_stride = max(1, int(round(step / max(lon_res, 1e-6))))

        features: List[Dict[str, Any]] = []
        valid_values: List[float] = []

        sub_rows = list(range(0, height, row_stride))
        sub_cols = list(range(0, width, col_stride))

        for r in sub_rows:
            for c in sub_cols:
                raw_val = float(data_2d[r, c])
                if np.isnan(raw_val):
                    continue

                if v_min is not None and raw_val < v_min:
                    continue
                if v_max is not None and raw_val > v_max:
                    continue

                lat = float(lats_2d[r, c])
                lon = float(lons_2d[r, c])

                val = round(raw_val, 2)
                valid_values.append(val)

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(lon, 4), round(lat, 4)]
                    },
                    "properties": {
                        "variable": var_name,
                        "value": val,
                        "raw_value": round(raw_val, 3),
                        "units": target_units,
                        "date": date_str,
                        "interpolated": bool(is_interpolated)
                    }
                }
                features.append(feature)

        stats = {}
        if valid_values:
            stats = {
                "min": round(float(np.min(valid_values)), 2),
                "max": round(float(np.max(valid_values)), 2),
                "mean": round(float(np.mean(valid_values)), 2),
                "count": len(valid_values)
            }

        metadata = {
            "dataset": f"nasa_modis_{var_name}",
            "source": "NASA Earth Engine (MODIS-Aqua L3SMI)",
            "variable": var_name,
            "description": config.get("description", var_name),
            "date": date_str,
            "units": target_units,
            "crs": crs_str,
            "bounds": [
                round(float(np.min(lons_2d)), 4),
                round(float(np.min(lats_2d)), 4),
                round(float(np.max(lons_2d)), 4),
                round(float(np.max(lats_2d)), 4)
            ],
            "stats": stats,
            "grid_step_deg": step,
            "feature_count": len(features),
            "interpolated": bool(is_interpolated),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }

        return {
            "type": "FeatureCollection",
            "metadata": metadata,
            "features": features
        }

    def process_file(
        self,
        file_path: Union[str, Path],
        variable_type: Optional[str] = None,
        date_str: Optional[str] = None,
        interpolate_missing: bool = True,
        grid_step: Optional[float] = None,
        upload_to_b2: bool = False,
        remote_b2_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a local GeoTIFF file into lightweight vector GeoJSON tiles.

        Args:
            file_path: Path to local GeoTIFF file.
            variable_type: Optional explicit variable type ('sst', 'chlor_a').
            date_str: Observation date (YYYY-MM-DD). If omitted, inferred from filename.
            interpolate_missing: Whether to apply spatial interpolation to cloud/missing gaps.
            grid_step: Downsampling grid step in degrees.
            upload_to_b2: Whether to upload resulting GeoJSON tile to Backblaze B2.
            remote_b2_key: Optional override for remote B2 key.

        Returns:
            Dictionary with processing status, output path, B2 key, and metadata.
        """
        path = Path(file_path)
        with self.open_raster(path) as src:
            # Metadata & CRS
            crs_str = str(src.crs) if src.crs else "EPSG:4326"
            nodata_val = src.nodata
            transform = src.transform
            width = src.width
            height = src.height

            # Infer date
            if not date_str:
                date_str = self._infer_date(path)

            # Identify variable type
            var_name, config = self.identify_band_type(path, src.tags(), variable_type)

            # Read primary band (Band 1)
            raw_data = src.read(1).astype(np.float64)

            # Build 2D coordinates matrix using affine transform
            cols, rows = np.meshgrid(np.arange(width), np.arange(height))
            lons_1d, lats_1d = xy(transform, rows, cols, offset="center")
            lons_2d = np.array(lons_1d, dtype=np.float64).reshape((height, width))
            lats_2d = np.array(lats_1d, dtype=np.float64).reshape((height, width))

            # Mask nodata values and invalid extremes
            effective_nodata = nodata_val if nodata_val is not None else config.get("default_nodata", -9999.0)
            data_2d = np.where(np.isclose(raw_data, effective_nodata) | (raw_data <= -9000), np.nan, raw_data)

            # Interpolation of cloud cover / missing data gaps
            interpolated = False
            interp_count = 0
            if interpolate_missing:
                v_min = config.get("valid_min")
                v_max = config.get("valid_max")
                data_2d, interp_count = self.interpolate_cloud_gaps(
                    data_2d, lats_2d, lons_2d, valid_min=v_min, valid_max=v_max
                )
                interpolated = interp_count > 0

            # Convert to lightweight vector GeoJSON
            geojson = self.convert_to_vector_geojson(
                data_2d=data_2d,
                lats_2d=lats_2d,
                lons_2d=lons_2d,
                var_name=var_name,
                config=config,
                date_str=date_str,
                crs_str=crs_str,
                is_interpolated=interpolated,
                grid_step=grid_step
            )

            # Save locally
            out_filename = f"{var_name}_nasa_{date_str}.geojson"
            local_out = self.staging_dir / out_filename
            with open(local_out, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)

            file_size = local_out.stat().st_size
            feature_count = len(geojson.get("features", []))
            logger.info(f"Generated vector GeoJSON: {local_out} ({feature_count} features, {file_size} bytes)")

            # Index with VectorIndexer
            indexer = VectorIndexer()
            indexer.index_geojson(geojson)

            # Upload to B2 if requested
            b2_upload_res = None
            target_b2_key = remote_b2_key or config.get("b2_tile_template", "").format(date=date_str)
            if upload_to_b2 and target_b2_key:
                b2_upload_res = self.b2_manager.upload_file(
                    file_path=str(local_out),
                    remote_key=target_b2_key,
                    content_type="application/geo+json"
                )
                logger.info(f"Uploaded GeoJSON tile to B2: b2://{self.b2_manager.bucket_name}/{target_b2_key}")

            # Record freshness in PostgreSQL
            try:
                from pipeline.storage.db_writer import DBWriter
                db = DBWriter(mock_mode=self.mock_mode)
                db.record_success(
                    dataset_name=f"nasa_modis_{var_name}",
                    record_count=feature_count,
                    file_size_bytes=file_size,
                    source_info={"source": "NASA Earth Engine", "input_file": path.name},
                    extra_metadata={"b2_key": target_b2_key, "interpolated": bool(interpolated)}
                )
            except Exception as dbe:
                logger.debug(f"Freshness tracking notice: {dbe}")

            return {
                "status": "success",
                "processor": "GeoTIFFProcessor",
                "variable": var_name,
                "date": date_str,
                "feature_count": feature_count,
                "file_size_bytes": file_size,
                "local_path": str(local_out),
                "b2_key": target_b2_key if upload_to_b2 else None,
                "b2_upload": b2_upload_res,
                "interpolated_points": interp_count,
                "metadata": geojson.get("metadata", {})
            }

    def process_from_b2(
        self,
        remote_b2_key: str,
        variable_type: Optional[str] = None,
        date_str: Optional[str] = None,
        interpolate_missing: bool = True,
        grid_step: Optional[float] = None,
        upload_to_b2: bool = True
    ) -> Dict[str, Any]:
        """
        Download a raw GeoTIFF file from B2, process it into vector GeoJSON, and upload the result.
        """
        local_dest = self.staging_dir / Path(remote_b2_key).name
        logger.info(f"Downloading raw GeoTIFF from B2: {remote_b2_key} -> {local_dest}")
        self.b2_manager.download_file(remote_b2_key, str(local_dest))

        return self.process_file(
            file_path=local_dest,
            variable_type=variable_type,
            date_str=date_str,
            interpolate_missing=interpolate_missing,
            grid_step=grid_step,
            upload_to_b2=upload_to_b2
        )

    def _infer_date(self, path: Path) -> str:
        """Infer date string (YYYY-MM-DD) from filename."""
        import re
        match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
        if match:
            return match.group(1)
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def run_demo():
    """Run demonstration with real existing NASA GEE GeoTIFF files."""
    print("=" * 70)
    print("DEMO: SCIENTIFIC GEOTIFF RASTER PROCESSOR (CHUNK_ID: R4-C07)")
    print("=" * 70)

    processor = GeoTIFFProcessor()

    candidates = [
        PROJECT_ROOT / "staging" / "nasa_gee" / "modis_aqua_sst_2026-09-13.tif",
        PROJECT_ROOT / "staging" / "nasa_gee" / "modis_aqua_chlor_a_2026-09-13.tif",
    ]

    target = None
    for cand in candidates:
        if cand.is_file():
            target = cand
            break

    if not target:
        print("No local NASA GeoTIFF file found. Attempting B2 download...")
        res = processor.process_from_b2(
            remote_b2_key="satellite/sst/nasa-modis/2026-09-13.tif",
            variable_type="sst",
            upload_to_b2=True
        )
    else:
        print(f"Processing real local GeoTIFF file: {target}")
        res = processor.process_file(
            file_path=target,
            variable_type="sst",
            upload_to_b2=True
        )

    print("\nProcessing Result:")
    for k, v in res.items():
        if k != "metadata":
            print(f"  {k:<20}: {v}")
    print("\nMetadata:")
    for k, v in res.get("metadata", {}).items():
        print(f"  {k:<20}: {v}")

    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process scientific GeoTIFF files into vector GeoJSON tiles.")
    parser.add_argument("--input", type=str, help="Path to local GeoTIFF file.")
    parser.add_argument("--b2-key", type=str, help="Remote B2 key to download and process.")
    parser.add_argument("--variable", type=str, choices=["sst", "chlor_a"], help="Variable type.")
    parser.add_argument("--date", type=str, help="Observation date (YYYY-MM-DD).")
    parser.add_argument("--grid-step", type=float, default=0.25, help="Downsampled grid resolution in degrees.")
    parser.add_argument("--upload", action="store_true", help="Upload resulting GeoJSON to B2.")
    parser.add_argument("--no-interpolate", action="store_true", help="Disable spatial interpolation.")

    args = parser.parse_args()

    if args.input or args.b2_key:
        proc = GeoTIFFProcessor(default_grid_step=args.grid_step)
        if args.b2_key:
            res = proc.process_from_b2(
                remote_b2_key=args.b2_key,
                variable_type=args.variable,
                date_str=args.date,
                interpolate_missing=not args.no_interpolate,
                upload_to_b2=args.upload
            )
        else:
            res = proc.process_file(
                file_path=args.input,
                variable_type=args.variable,
                date_str=args.date,
                interpolate_missing=not args.no_interpolate,
                upload_to_b2=args.upload
            )
        print(json.dumps(res, indent=2, default=str))
    else:
        run_demo()
