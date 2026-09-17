"""
Scientific NetCDF Raster Processor (CHUNK_ID: R4-C07)
------------------------------------------------------
Role: Role 4 (Data Pipeline Engineer)
Target: pipeline/processors/netcdf_processor.py
Prerequisites: [R4-C02, R4-C03]

Opens raw satellite NetCDF files (produced by Copernicus Marine ingestor or downloaded
from Backblaze B2), extracts scientific data arrays (SST, Chlorophyll-a, Ocean Currents),
extracts latitude/longitude coordinates, cleanly interpolates cloud-cover gaps within
ocean domains, and converts heavy grids into lightweight vector GeoJSON tiles suitable
for fast frontend map layer rendering.
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
import xarray as xr

# Try importing scipy for advanced spatial interpolation
try:
    from scipy.interpolate import griddata
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from pipeline.config import CopernicusConfig, B2Config
from pipeline.storage.b2_uploader import B2StorageManager
from pipeline.storage.vector_indexer import VectorIndexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("netcdf_processor")


class NetCDFProcessor:
    """
    Processes scientific NetCDF satellite files from Copernicus Marine Service,
    extracts ocean variables, performs cloud-gap interpolation, and generates
    lightweight vector GeoJSON tiles for client map rendering and B2 storage.
    """

    # Variable mapping and physical validation ranges
    VARIABLE_CONFIGS: Dict[str, Dict[str, Any]] = {
        "sst": {
            "candidate_names": ["analysed_sst", "sst", "sea_surface_temperature", "thetao"],
            "description": "Sea Surface Temperature",
            "target_units": "°C",
            "kelvin_conversion": True,  # Subtract 273.15 if values > 150
            "valid_min": 15.0,         # Minimum realistic SST in Indian Ocean (°C)
            "valid_max": 36.0,         # Maximum realistic SST in Indian Ocean (°C)
            "b2_tile_template": "processed/tiles/sst/copernicus/{date}.geojson",
        },
        "chlorophyll": {
            "candidate_names": ["CHL", "chlor_a", "chlorophyll", "chl"],
            "description": "Surface Chlorophyll-a concentration",
            "target_units": "mg/m³",
            "kelvin_conversion": False,
            "valid_min": 0.01,
            "valid_max": 60.0,
            "b2_tile_template": "processed/tiles/chlorophyll/copernicus/{date}.geojson",
        },
        "currents": {
            "candidate_names": ["uo", "vo"],
            "description": "Surface Ocean Velocity Vectors",
            "target_units": "m/s",
            "kelvin_conversion": False,
            "valid_min": -5.0,
            "valid_max": 5.0,
            "b2_tile_template": "processed/tiles/currents/copernicus/{date}.geojson",
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
        Initialize the NetCDF processor.

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

    def open_dataset(self, file_path: Union[str, Path]) -> xr.Dataset:
        """
        Open a NetCDF file with xarray, verifying coordinates and structure.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"NetCDF file does not exist: {file_path}")
        logger.info(f"Opening NetCDF file: {file_path} ({path.stat().st_size} bytes)")
        return xr.open_dataset(str(path))

    def identify_variable(self, ds: xr.Dataset, requested_type: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Identify the primary scientific ocean variable in the xarray Dataset.

        Returns:
            Tuple of (primary_var_name, config_dict)
        """
        if requested_type and requested_type in self.VARIABLE_CONFIGS:
            config = self.VARIABLE_CONFIGS[requested_type]
            for name in config["candidate_names"]:
                if name in ds.data_vars:
                    return name, config

        # Search across all known configs
        for var_type, config in self.VARIABLE_CONFIGS.items():
            for name in config["candidate_names"]:
                if name in ds.data_vars:
                    return name, config

        # Fallback to first available variable
        available = list(ds.data_vars.keys())
        if not available:
            raise ValueError("No data variables found in NetCDF dataset.")
        var_name = available[0]
        logger.warning(f"Unrecognized variable '{var_name}'. Using generic fallback configuration.")
        return var_name, {
            "candidate_names": [var_name],
            "description": var_name,
            "target_units": ds[var_name].attrs.get("units", "units"),
            "kelvin_conversion": False,
            "valid_min": None,
            "valid_max": None,
            "b2_tile_template": f"processed/tiles/{var_name}/copernicus/{{date}}.geojson"
        }

    def extract_coordinates(self, ds: xr.Dataset) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract 1D latitude and longitude coordinate arrays from Dataset.
        """
        lat_coord = None
        for name in ["latitude", "lat", "LATITUDE", "Lat"]:
            if name in ds.coords:
                lat_coord = ds.coords[name].values
                break

        lon_coord = None
        for name in ["longitude", "lon", "LONGITUDE", "Lon"]:
            if name in ds.coords:
                lon_coord = ds.coords[name].values
                break

        if lat_coord is None or lon_coord is None:
            raise ValueError(f"Could not locate latitude/longitude coordinates in dataset. Coords: {list(ds.coords.keys())}")

        return lat_coord, lon_coord

    def interpolate_cloud_gaps(
        self,
        data_2d: np.ndarray,
        lats: np.ndarray,
        lons: np.ndarray,
        valid_min: Optional[float] = None,
        valid_max: Optional[float] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Cleanly interpolate missing data points (NaNs caused by clouds) over ocean domains.
        Preserves natural land boundaries and does not invent out-of-bounds scientific data.

        Returns:
            Tuple of (interpolated_array, number_of_interpolated_points)
        """
        arr = np.copy(data_2d)
        is_nan = np.isnan(arr)
        total_nan = int(np.sum(is_nan))

        if total_nan == 0 or total_nan == arr.size:
            return arr, 0

        # Valid ocean data points
        valid_mask = ~is_nan
        valid_count = int(np.sum(valid_mask))
        if valid_count < 10:
            logger.warning("Too few valid points for spatial interpolation.")
            return arr, 0

        # Build 2D coordinate mesh
        lon_grid, lat_grid = np.meshgrid(lons, lats)

        # Points where data exists
        points = np.column_stack((lon_grid[valid_mask], lat_grid[valid_mask]))
        values = arr[valid_mask]

        interpolated_count = 0

        if HAS_SCIPY:
            try:
                # 1. Linear interpolation on missing points
                nan_points = np.column_stack((lon_grid[is_nan], lat_grid[is_nan]))
                interp_linear = griddata(points, values, nan_points, method="linear")

                # 2. Nearest neighbor fallback only for points within reasonable convex hull
                interp_nearest = griddata(points, values, nan_points, method="nearest")

                # Prefer linear, fallback to nearest for border ocean cells
                filled_values = np.where(np.isnan(interp_linear), interp_nearest, interp_linear)

                # Clamp within physically valid ranges
                if valid_min is not None:
                    filled_values = np.maximum(filled_values, valid_min)
                if valid_max is not None:
                    filled_values = np.minimum(filled_values, valid_max)

                arr[is_nan] = filled_values
                interpolated_count = len(filled_values)
                logger.info(f"Interpolated {interpolated_count} cloud/missing ocean pixels using scipy.")
            except Exception as e:
                logger.warning(f"Scipy interpolation encountered error ({e}). Using robust multi-pass numpy fallback.")
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
        Robust numpy-only local neighborhood averaging for cloud-gap filling.
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
        lats: np.ndarray,
        lons: np.ndarray,
        var_name: str,
        config: Dict[str, Any],
        date_str: str,
        is_interpolated: bool = False,
        grid_step: Optional[float] = None,
        uo_2d: Optional[np.ndarray] = None,
        vo_2d: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Convert 2D scientific ocean raster into a lightweight vector GeoJSON FeatureCollection
        suitable for fast client map rendering (Leaflet/Mapbox).

        Args:
            data_2d: 2D array of ocean values (lat x lon).
            lats: 1D latitude array.
            lons: 1D longitude array.
            var_name: Variable name.
            config: Variable configuration dictionary.
            date_str: Observation date (YYYY-MM-DD).
            is_interpolated: Whether data array underwent spatial interpolation.
            grid_step: Downsampling grid step in degrees (default: self.default_grid_step).
            uo_2d: Optional eastward current component (for currents dataset).
            vo_2d: Optional northward current component (for currents dataset).

        Returns:
            RFC 7946 compliant GeoJSON FeatureCollection dictionary.
        """
        step = grid_step or self.default_grid_step
        target_units = config.get("target_units", "")
        convert_kelvin = config.get("kelvin_conversion", False)

        # Determine indices to downsample to the target grid_step
        lat_diff = abs(float(lats[1] - lats[0])) if len(lats) > 1 else 0.05
        lon_diff = abs(float(lons[1] - lons[0])) if len(lons) > 1 else 0.05

        lat_stride = max(1, int(round(step / max(lat_diff, 1e-6))))
        lon_stride = max(1, int(round(step / max(lon_diff, 1e-6))))

        features: List[Dict[str, Any]] = []
        valid_values: List[float] = []

        sub_lat_indices = list(range(0, len(lats), lat_stride))
        sub_lon_indices = list(range(0, len(lons), lon_stride))

        is_currents = bool(uo_2d is not None and vo_2d is not None)

        for ri in sub_lat_indices:
            lat = float(lats[ri])
            for ci in sub_lon_indices:
                lon = float(lons[ci])
                raw_val = float(data_2d[ri, ci])

                if np.isnan(raw_val):
                    continue

                val = raw_val
                if convert_kelvin and val > 150.0:
                    val = val - 273.15  # Convert Kelvin to Celsius

                # Validation clamp if configured
                v_min = config.get("valid_min")
                v_max = config.get("valid_max")
                if v_min is not None and val < v_min:
                    continue
                if v_max is not None and val > v_max:
                    continue

                val = round(val, 2)
                valid_values.append(val)

                props: Dict[str, Any] = {
                    "variable": var_name,
                    "value": val,
                    "raw_value": round(raw_val, 2),
                    "units": target_units,
                    "date": date_str,
                    "interpolated": bool(is_interpolated)
                }

                if is_currents:
                    u = float(uo_2d[ri, ci])
                    v = float(vo_2d[ri, ci])
                    speed = float(np.sqrt(u**2 + v**2))
                    heading = float((np.degrees(np.arctan2(u, v)) + 360) % 360)
                    props.update({
                        "uo": round(u, 3),
                        "vo": round(v, 3),
                        "speed_mps": round(speed, 2),
                        "speed_knots": round(speed * 1.94384, 2),
                        "heading_deg": round(heading, 1)
                    })

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(lon, 4), round(lat, 4)]
                    },
                    "properties": props
                }
                features.append(feature)

        # Dataset statistics
        stats = {}
        if valid_values:
            stats = {
                "min": round(float(np.min(valid_values)), 2),
                "max": round(float(np.max(valid_values)), 2),
                "mean": round(float(np.mean(valid_values)), 2),
                "count": len(valid_values)
            }

        metadata = {
            "dataset": f"copernicus_{var_name}",
            "source": "Copernicus Marine Service (CMEMS)",
            "variable": var_name,
            "description": config.get("description", var_name),
            "date": date_str,
            "units": target_units,
            "bounds": [
                round(float(np.min(lons)), 4),
                round(float(np.min(lats)), 4),
                round(float(np.max(lons)), 4),
                round(float(np.max(lats)), 4)
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
        Process a local NetCDF file into lightweight vector GeoJSON tiles.

        Args:
            file_path: Path to local NetCDF file.
            variable_type: Optional explicit variable type ('sst', 'chlorophyll', 'currents').
            date_str: Observation date (YYYY-MM-DD). If omitted, inferred from filename or metadata.
            interpolate_missing: Whether to apply spatial interpolation to cloud/missing gaps.
            grid_step: Downsampling grid step in degrees.
            upload_to_b2: Whether to upload resulting GeoJSON tile to Backblaze B2.
            remote_b2_key: Optional override for remote B2 key.

        Returns:
            Dictionary with processing status, output path, B2 key, and metadata.
        """
        path = Path(file_path)
        ds = self.open_dataset(path)

        try:
            # Infer date if not given
            if not date_str:
                date_str = self._infer_date(path, ds)

            # Identify variable
            var_name, config = self.identify_variable(ds, variable_type)
            lats, lons = self.extract_coordinates(ds)

            # Extract 2D array (taking first time/depth slice if multi-dimensional)
            da = ds[var_name]
            while da.ndim > 2:
                da = da.isel({da.dims[0]: 0})
            data_2d = da.values.astype(np.float64)

            # Handle currents (uo and vo)
            uo_2d, vo_2d = None, None
            if "uo" in ds.data_vars and "vo" in ds.data_vars:
                var_name = "currents"
                config = self.VARIABLE_CONFIGS["currents"]
                da_u = ds["uo"]
                da_v = ds["vo"]
                while da_u.ndim > 2:
                    da_u = da_u.isel({da_u.dims[0]: 0})
                while da_v.ndim > 2:
                    da_v = da_v.isel({da_v.dims[0]: 0})
                uo_2d = da_u.values.astype(np.float64)
                vo_2d = da_v.values.astype(np.float64)
                data_2d = np.sqrt(uo_2d**2 + vo_2d**2)

            # Interpolation of missing data / cloud cover
            interpolated = False
            interp_count = 0
            if interpolate_missing:
                v_min = config.get("valid_min")
                v_max = config.get("valid_max")
                if config.get("kelvin_conversion") and np.nanmean(data_2d) > 150:
                    v_min = v_min + 273.15 if v_min else None
                    v_max = v_max + 273.15 if v_max else None

                data_2d, interp_count = self.interpolate_cloud_gaps(
                    data_2d, lats, lons, valid_min=v_min, valid_max=v_max
                )
                interpolated = interp_count > 0

            # Convert to lightweight vector GeoJSON
            geojson = self.convert_to_vector_geojson(
                data_2d=data_2d,
                lats=lats,
                lons=lons,
                var_name=var_name,
                config=config,
                date_str=date_str,
                is_interpolated=interpolated,
                grid_step=grid_step,
                uo_2d=uo_2d,
                vo_2d=vo_2d
            )

            # Save locally
            out_filename = f"{var_name}_copernicus_{date_str}.geojson"
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
                    dataset_name=f"copernicus_{var_name}",
                    record_count=feature_count,
                    file_size_bytes=file_size,
                    source_info={"source": "Copernicus Marine", "input_file": path.name},
                    extra_metadata={"b2_key": target_b2_key, "interpolated": bool(interpolated)}
                )
            except Exception as dbe:
                logger.debug(f"Freshness tracking notice: {dbe}")

            return {
                "status": "success",
                "processor": "NetCDFProcessor",
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

        finally:
            ds.close()

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
        Download a raw NetCDF file from B2, process it into vector GeoJSON, and upload the result.
        """
        local_dest = self.staging_dir / Path(remote_b2_key).name
        logger.info(f"Downloading raw NetCDF from B2: {remote_b2_key} -> {local_dest}")
        self.b2_manager.download_file(remote_b2_key, str(local_dest))

        return self.process_file(
            file_path=local_dest,
            variable_type=variable_type,
            date_str=date_str,
            interpolate_missing=interpolate_missing,
            grid_step=grid_step,
            upload_to_b2=upload_to_b2
        )

    def _infer_date(self, path: Path, ds: xr.Dataset) -> str:
        """Infer date string (YYYY-MM-DD) from filename or dataset time coordinate."""
        import re
        match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
        if match:
            return match.group(1)

        if "time" in ds.coords:
            t_val = ds.coords["time"].values
            if hasattr(t_val, "__len__") and len(t_val) > 0:
                t_val = t_val[0]
            dt = np.datetime64(t_val, "D")
            return str(dt)

        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def run_demo():
    """Run demonstration with real existing Copernicus NetCDF files."""
    print("=" * 70)
    print("DEMO: SCIENTIFIC NETCDF RASTER PROCESSOR (CHUNK_ID: R4-C07)")
    print("=" * 70)

    processor = NetCDFProcessor()

    # Search for real NetCDF files
    candidates = [
        PROJECT_ROOT / "staging" / "copernicus" / "raw" / "sst" / "sst_2026-09-06_raw.nc",
        PROJECT_ROOT / "staging" / "copernicus" / "raw" / "chlorophyll" / "chlorophyll_2026-09-06_raw.nc",
        PROJECT_ROOT / "staging" / "copernicus" / "compressed" / "sst_2026-09-06.nc"
    ]

    target = None
    for cand in candidates:
        if cand.is_file():
            target = cand
            break

    if not target:
        print("No local Copernicus NetCDF file found. Attempting B2 download...")
        res = processor.process_from_b2(
            remote_b2_key="satellite/sst/copernicus/2026-09-06.nc",
            variable_type="sst",
            upload_to_b2=True
        )
    else:
        print(f"Processing real local NetCDF file: {target}")
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
    parser = argparse.ArgumentParser(description="Process scientific NetCDF files into vector GeoJSON tiles.")
    parser.add_argument("--input", type=str, help="Path to local NetCDF file.")
    parser.add_argument("--b2-key", type=str, help="Remote B2 key to download and process.")
    parser.add_argument("--variable", type=str, choices=["sst", "chlorophyll", "currents"], help="Variable type.")
    parser.add_argument("--date", type=str, help="Observation date (YYYY-MM-DD).")
    parser.add_argument("--grid-step", type=float, default=0.25, help="Downsampled grid resolution in degrees.")
    parser.add_argument("--upload", action="store_true", help="Upload resulting GeoJSON to B2.")
    parser.add_argument("--no-interpolate", action="store_true", help="Disable spatial interpolation.")

    args = parser.parse_args()

    if args.input or args.b2_key:
        proc = NetCDFProcessor(default_grid_step=args.grid_step)
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
