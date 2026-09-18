from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import requests
import xarray as xr
try:
    from langchain_core.tools import tool
except ImportError:
    def tool(fn=None):
        if fn is None:
            return lambda f: tool(f)
        fn.invoke = lambda args: fn(**args) if isinstance(args, dict) else fn(args)
        return fn


# NASA OceanColor / MODIS-Aqua data
NASA_OCEANCOLOR_URL = (
    "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/"
)

REQUEST_TIMEOUT = 30


def _validate_coordinates(
    latitude: float,
    longitude: float,
) -> None:
    """Validate geographic coordinates."""

    if not -90 <= latitude <= 90:
        raise ValueError(f"Invalid latitude: {latitude}")

    if not -180 <= longitude <= 180:
        raise ValueError(f"Invalid longitude: {longitude}")


@tool
def get_sst_data(
    latitude: float,
    longitude: float,
    file_path: str,
) -> dict[str, Any]:
    """
    Read sea surface temperature from a local NetCDF dataset
    and return the value nearest to the requested coordinates.

    Supports:
    - sst
    - sea_surface_temperature
    - analysed_sst
    - sst4

    Supports coordinate names:
    - lat / lon
    - latitude / longitude
    - y / x
    """

    _validate_coordinates(latitude, longitude)

    path = Path(file_path)

    if not path.exists():
        return {
            "source": "NASA_MODIS_SST",
            "latitude": latitude,
            "longitude": longitude,
            "sst_celsius": None,
            "status": "error",
            "error": f"Dataset not found: {file_path}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        with xr.open_dataset(path, engine="netcdf4") as ds:

            # -------------------------------------------------
            # Find SST variable
            # -------------------------------------------------

            variable_name = None

            for candidate in [
                "sst",
                "sea_surface_temperature",
                "analysed_sst",
                "sst4",
            ]:
                if candidate in ds.data_vars:
                    variable_name = candidate
                    break

            if variable_name is None:
                return {
                    "source": "NASA_MODIS_SST",
                    "latitude": latitude,
                    "longitude": longitude,
                    "sst_celsius": None,
                    "status": "error",
                    "error": (
                        "No supported SST variable found in dataset."
                    ),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            sst = ds[variable_name]

            # -------------------------------------------------
            # Find latitude / longitude coordinate names
            # -------------------------------------------------

            lat_name = next(
                (
                    name
                    for name in ["lat", "latitude", "y"]
                    if name in sst.coords
                ),
                None,
            )

            lon_name = next(
                (
                    name
                    for name in ["lon", "longitude", "x"]
                    if name in sst.coords
                ),
                None,
            )

            if lat_name is None or lon_name is None:
                return {
                    "source": "NASA_MODIS_SST",
                    "latitude": latitude,
                    "longitude": longitude,
                    "sst_celsius": None,
                    "status": "error",
                    "error": (
                        "Latitude/longitude coordinates not found."
                    ),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            # -------------------------------------------------
            # Select nearest grid cell
            # -------------------------------------------------

            selected = sst.sel(
                {
                    lat_name: latitude,
                    lon_name: longitude,
                },
                method="nearest",
            )

            selected = selected.squeeze(drop=True)

            value = np.asarray(selected.values).squeeze()

            if value.size == 0 or not np.isfinite(value).any():
                return {
                    "source": "NASA_MODIS_SST",
                    "latitude": latitude,
                    "longitude": longitude,
                    "sst_celsius": None,
                    "status": "no_data",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            sst_value = float(value)

            # -------------------------------------------------
            # Convert Kelvin to Celsius when necessary
            # -------------------------------------------------

            units = str(
                sst.attrs.get("units", "")
            ).lower()

            if "kelvin" in units or units in {"k", "degk"}:
                sst_value -= 273.15

            elif sst_value > 100:
                # Safety fallback for datasets whose
                # units metadata is missing.
                sst_value -= 273.15

            # -------------------------------------------------
            # Actual grid coordinates
            # -------------------------------------------------

            actual_lat = float(
                selected[lat_name].values
            )

            actual_lon = float(
                selected[lon_name].values
            )

            # -------------------------------------------------
            # Successful result
            # -------------------------------------------------

            return {
                "source": "NASA_MODIS_SST",
                "latitude": latitude,
                "longitude": longitude,
                "data_latitude": actual_lat,
                "data_longitude": actual_lon,
                "sst_celsius": sst_value,
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as exc:
        return {
            "source": "NASA_MODIS_SST",
            "latitude": latitude,
            "longitude": longitude,
            "sst_celsius": None,
            "status": "error",
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@tool
def get_chlorophyll_data(
    latitude: float,
    longitude: float,
    file_path: str,
) -> dict[str, Any]:
    """
    Get chlorophyll-a concentration from a NetCDF file.

    Supports:
    - R3/NASA data: chlor_a
    - R4/Copernicus data: CHL

    Supports coordinate names:
    - lat / lon
    - latitude / longitude
    """

    # ---------------------------------------------------------
    # 1. Validate coordinates
    # ---------------------------------------------------------

    if not -90.0 <= latitude <= 90.0:
        return {
            "source": "NASA_MODIS_CHLOROPHYLL",
            "status": "error",
            "error": "Latitude must be between -90 and 90 degrees.",
        }

    if not -180.0 <= longitude <= 180.0:
        return {
            "source": "NASA_MODIS_CHLOROPHYLL",
            "status": "error",
            "error": "Longitude must be between -180 and 180 degrees.",
        }

    # ---------------------------------------------------------
    # 2. Check file
    # ---------------------------------------------------------

    path = Path(file_path)

    if not path.exists():
        return {
            "source": "NASA_MODIS_CHLOROPHYLL",
            "status": "error",
            "error": f"File not found: {file_path}",
        }

    # ---------------------------------------------------------
    # 3. Open dataset
    # ---------------------------------------------------------

    try:
        with xr.open_dataset(
            path,
            engine="netcdf4",
        ) as ds:

            # -------------------------------------------------
            # Find chlorophyll variable
            # -------------------------------------------------

            if "chlor_a" in ds:
                chlor_a = ds["chlor_a"]

            elif "CHL" in ds:
                chlor_a = ds["CHL"]

            else:
                return {
                    "source": "NASA_MODIS_CHLOROPHYLL",
                    "status": "error",
                    "error": (
                        "Neither chlor_a nor CHL variable "
                        "found in dataset."
                    ),
                }

            # -------------------------------------------------
            # Find coordinate names
            # -------------------------------------------------

            if (
                "lat" in chlor_a.coords
                and "lon" in chlor_a.coords
            ):
                lat_name = "lat"
                lon_name = "lon"

            elif (
                "latitude" in chlor_a.coords
                and "longitude" in chlor_a.coords
            ):
                lat_name = "latitude"
                lon_name = "longitude"

            else:
                return {
                    "source": "NASA_MODIS_CHLOROPHYLL",
                    "status": "error",
                    "error": (
                        "Dataset does not contain supported "
                        "lat/lon coordinates."
                    ),
                }

            # -------------------------------------------------
            # Select nearest grid cell
            # -------------------------------------------------

            selected = chlor_a.sel(
                {
                    lat_name: latitude,
                    lon_name: longitude,
                },
                method="nearest",
            )

            selected = selected.squeeze(drop=True)

            value = float(
                np.asarray(selected.values).squeeze()
            )

            actual_lat = float(
                selected[lat_name].values
            )

            actual_lon = float(
                selected[lon_name].values
            )

            # -------------------------------------------------
            # Handle missing data
            # -------------------------------------------------

            if not np.isfinite(value):
                return {
                    "source": "NASA_MODIS_CHLOROPHYLL",
                    "latitude": latitude,
                    "longitude": longitude,
                    "data_latitude": actual_lat,
                    "data_longitude": actual_lon,
                    "chlorophyll_mg_m3": None,
                    "status": "no_data",
                    "message": (
                        "No valid chlorophyll observation "
                        "at the nearest grid cell."
                    ),
                }

            # -------------------------------------------------
            # Validate scientific range
            # -------------------------------------------------

            if value < 0.001 or value > 100.0:
                return {
                    "source": "NASA_MODIS_CHLOROPHYLL",
                    "latitude": latitude,
                    "longitude": longitude,
                    "data_latitude": actual_lat,
                    "data_longitude": actual_lon,
                    "chlorophyll_mg_m3": None,
                    "status": "invalid_data",
                    "message": (
                        "Chlorophyll value is outside "
                        "the valid range."
                    ),
                }

            # -------------------------------------------------
            # Successful result
            # -------------------------------------------------

            return {
                "source": "NASA_MODIS_CHLOROPHYLL",
                "latitude": latitude,
                "longitude": longitude,
                "data_latitude": actual_lat,
                "data_longitude": actual_lon,
                "chlorophyll_mg_m3": value,
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as exc:
        return {
            "source": "NASA_MODIS_CHLOROPHYLL",
            "latitude": latitude,
            "longitude": longitude,
            "status": "error",
            "error": str(exc),
        }


@tool
def detect_thermal_front(
    file_path: str,
    latitude: float,
    longitude: float,
    gradient_threshold_c_per_km: float = 0.05,
) -> dict[str, Any]:
    """
    Detect a possible thermal front near a requested location.

    Supports:
    - R3 test data: sst + lat/lon + optional qual_sst
    - R4 Copernicus: analysed_sst + latitude/longitude

    If qual_sst is available, it is used as a quality mask.

    If qual_sst is unavailable, only finite SST values
    are used.
    """

    # ---------------------------------------------------------
    # 1. Validate coordinates
    # ---------------------------------------------------------

    if not -90.0 <= latitude <= 90.0:
        return {
            "source": "SST",
            "status": "error",
            "error": "Latitude must be between -90 and 90 degrees.",
        }

    if not -180.0 <= longitude <= 180.0:
        return {
            "source": "SST",
            "status": "error",
            "error": "Longitude must be between -180 and 180 degrees.",
        }

    # ---------------------------------------------------------
    # 2. Check file
    # ---------------------------------------------------------

    path = Path(file_path)

    if not path.exists():
        return {
            "source": "SST",
            "status": "error",
            "error": f"File not found: {file_path}",
        }

    # ---------------------------------------------------------
    # 3. Open dataset
    # ---------------------------------------------------------

    try:
        with xr.open_dataset(
            path,
            engine="netcdf4",
        ) as ds:

            # -------------------------------------------------
            # Find SST variable
            # -------------------------------------------------

            sst_name = next(
                (
                    name
                    for name in [
                        "sst",
                        "analysed_sst",
                        "sea_surface_temperature",
                        "sst4",
                    ]
                    if name in ds.data_vars
                ),
                None,
            )

            if sst_name is None:
                return {
                    "source": "SST",
                    "status": "error",
                    "error": (
                        "No supported SST variable "
                        "found in dataset."
                    ),
                }

            sst = ds[sst_name]

            # -------------------------------------------------
            # Find coordinate names
            # -------------------------------------------------

            lat_name = next(
                (
                    name
                    for name in [
                        "lat",
                        "latitude",
                        "y",
                    ]
                    if name in sst.coords
                ),
                None,
            )

            lon_name = next(
                (
                    name
                    for name in [
                        "lon",
                        "longitude",
                        "x",
                    ]
                    if name in sst.coords
                ),
                None,
            )

            if lat_name is None or lon_name is None:
                return {
                    "source": "SST",
                    "status": "error",
                    "error": (
                        "Latitude/longitude coordinates "
                        "not found."
                    ),
                }

            # -------------------------------------------------
            # Remove singleton dimensions such as time
            # -------------------------------------------------

            sst = sst.squeeze(drop=True)

            # -------------------------------------------------
            # Find nearest target pixel
            # -------------------------------------------------

            target = sst.sel(
                {
                    lat_name: latitude,
                    lon_name: longitude,
                },
                method="nearest",
            )

            target = target.squeeze(drop=True)

            target_lat = float(
                target[lat_name].values
            )

            target_lon = float(
                target[lon_name].values
            )

            target_sst = float(
                np.asarray(target.values).squeeze()
            )

            # -------------------------------------------------
            # Check target SST
            # -------------------------------------------------

            if not np.isfinite(target_sst):
                return {
                    "source": "SST",
                    "latitude": latitude,
                    "longitude": longitude,
                    "data_latitude": target_lat,
                    "data_longitude": target_lon,
                    "thermal_front_detected": False,
                    "status": "no_data",
                    "message": (
                        "No valid SST observation "
                        "at the requested grid cell."
                    ),
                }

            # -------------------------------------------------
            # Get grid indices
            # -------------------------------------------------

            lat_values_full = sst[lat_name].values
            lon_values_full = sst[lon_name].values

            lat_index = int(
                np.abs(
                    lat_values_full - target_lat
                ).argmin()
            )

            lon_index = int(
                np.abs(
                    lon_values_full - target_lon
                ).argmin()
            )

            # -------------------------------------------------
            # 3x3 neighborhood
            # -------------------------------------------------

            lat_start = max(
                0,
                lat_index - 1,
            )

            lat_end = min(
                len(lat_values_full),
                lat_index + 2,
            )

            lon_start = max(
                0,
                lon_index - 1,
            )

            lon_end = min(
                len(lon_values_full),
                lon_index + 2,
            )

            local_sst = sst.isel(
                {
                    lat_name: slice(
                        lat_start,
                        lat_end,
                    ),
                    lon_name: slice(
                        lon_start,
                        lon_end,
                    ),
                }
            )

            local_sst_values = np.asarray(
                local_sst.values
            ).squeeze()

            # -------------------------------------------------
            # Apply optional quality mask
            # -------------------------------------------------

            if "qual_sst" in ds.data_vars:
                quality = ds["qual_sst"].squeeze(
                    drop=True
                )

                local_quality = quality.isel(
                    {
                        lat_name: slice(
                            lat_start,
                            lat_end,
                        ),
                        lon_name: slice(
                            lon_start,
                            lon_end,
                        ),
                    }
                )

                local_quality_values = np.asarray(
                    local_quality.values
                ).squeeze()

                valid_mask = (
                    np.isfinite(local_sst_values)
                    & np.isfinite(
                        local_quality_values
                    )
                    & (
                        local_quality_values <= 2
                    )
                )

                quality_mode = "qual_sst"

            else:
                # R4 Copernicus analysed_sst does not
                # provide qual_sst.
                valid_mask = np.isfinite(
                    local_sst_values
                )

                quality_mode = "finite_sst_only"

            valid_sst = np.where(
                valid_mask,
                local_sst_values,
                np.nan,
            )

            # -------------------------------------------------
            # Need enough valid pixels
            # -------------------------------------------------

            valid_count = int(
                np.isfinite(valid_sst).sum()
            )

            if valid_count < 3:
                return {
                    "source": "SST",
                    "latitude": latitude,
                    "longitude": longitude,
                    "data_latitude": target_lat,
                    "data_longitude": target_lon,
                    "thermal_front_detected": False,
                    "gradient_c_per_km": None,
                    "status": "insufficient_data",
                    "valid_pixels": valid_count,
                    "quality_mode": quality_mode,
                }

            # -------------------------------------------------
            # Calculate local SST gradients
            # -------------------------------------------------

            lat_values = local_sst[lat_name].values
            lon_values = local_sst[lon_name].values

            gradients = []

            for i in range(
                local_sst.shape[0]
            ):

                for j in range(
                    local_sst.shape[1]
                ):

                    current = valid_sst[i, j]

                    if not np.isfinite(current):
                        continue

                    # -----------------------------------------
                    # North/South neighbor
                    # -----------------------------------------

                    if (
                        i + 1
                        < local_sst.shape[0]
                    ):

                        neighbor = valid_sst[
                            i + 1,
                            j,
                        ]

                        if np.isfinite(neighbor):

                            lat_distance_km = (
                                abs(
                                    lat_values[
                                        i + 1
                                    ]
                                    - lat_values[i]
                                )
                                * 111.32
                            )

                            if lat_distance_km > 0:

                                gradient = (
                                    abs(
                                        neighbor
                                        - current
                                    )
                                    / lat_distance_km
                                )

                                gradients.append(
                                    gradient
                                )

                    # -----------------------------------------
                    # East/West neighbor
                    # -----------------------------------------

                    if (
                        j + 1
                        < local_sst.shape[1]
                    ):

                        neighbor = valid_sst[
                            i,
                            j + 1,
                        ]

                        if np.isfinite(neighbor):

                            mean_lat = np.deg2rad(
                                (
                                    lat_values[i]
                                    + lat_values[i]
                                )
                                / 2
                            )

                            lon_distance_km = (
                                abs(
                                    lon_values[
                                        j + 1
                                    ]
                                    - lon_values[j]
                                )
                                * 111.32
                                * np.cos(
                                    mean_lat
                                )
                            )

                            if lon_distance_km > 0:

                                gradient = (
                                    abs(
                                        neighbor
                                        - current
                                    )
                                    / lon_distance_km
                                )

                                gradients.append(
                                    gradient
                                )

            # -------------------------------------------------
            # No gradients
            # -------------------------------------------------

            if not gradients:
                return {
                    "source": "SST",
                    "latitude": latitude,
                    "longitude": longitude,
                    "data_latitude": target_lat,
                    "data_longitude": target_lon,
                    "thermal_front_detected": False,
                    "gradient_c_per_km": None,
                    "status": "insufficient_data",
                    "valid_pixels": valid_count,
                    "quality_mode": quality_mode,
                }

            # -------------------------------------------------
            # Strongest local gradient
            # -------------------------------------------------

            max_gradient = float(
                max(gradients)
            )

            thermal_front_detected = (
                max_gradient
                >= gradient_threshold_c_per_km
            )

            return {
                "source": "SST",
                "latitude": latitude,
                "longitude": longitude,
                "data_latitude": target_lat,
                "data_longitude": target_lon,
                "gradient_c_per_km": max_gradient,
                "threshold_c_per_km": (
                    gradient_threshold_c_per_km
                ),
                "thermal_front_detected": (
                    thermal_front_detected
                ),
                "valid_pixels": valid_count,
                "quality_mode": quality_mode,
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as exc:
        return {
            "source": "SST",
            "latitude": latitude,
            "longitude": longitude,
            "status": "error",
            "error": str(exc),
        }


@tool
def calculate_pfz_suitability(
    chlorophyll_mg_m3: float | None,
    thermal_front_detected: bool,
    thermal_gradient_c_per_km: float | None = None,
) -> dict[str, Any]:
    """
    Calculate a deterministic PFZ suitability score from
    chlorophyll concentration and thermal-front detection.

    Returns a score from 0.0 to 1.0.
    """

    if chlorophyll_mg_m3 is None:
        return {
            "status": "no_data",
            "pfz_suitability_score": None,
            "classification": "UNKNOWN",
            "message": (
                "Chlorophyll data is unavailable."
            ),
        }

    if chlorophyll_mg_m3 < 0:
        return {
            "status": "error",
            "pfz_suitability_score": None,
            "classification": "UNKNOWN",
            "message": "Chlorophyll cannot be negative.",
        }

    # ---------------------------------------------------------
    # Chlorophyll score
    #
    # < 0.2       -> low
    # 0.2 - 1.0   -> moderate
    # > 1.0       -> high
    # ---------------------------------------------------------

    if chlorophyll_mg_m3 < 0.2:
        chlorophyll_score = 0.25
        chlorophyll_level = "LOW"

    elif chlorophyll_mg_m3 <= 1.0:
        chlorophyll_score = (
            0.25
            + (
                (chlorophyll_mg_m3 - 0.2)
                / 0.8
            )
            * 0.75
        )

        chlorophyll_level = "MODERATE"

    else:
        chlorophyll_score = 1.0
        chlorophyll_level = "HIGH"

    # ---------------------------------------------------------
    # Thermal-front score
    # ---------------------------------------------------------

    if thermal_front_detected:
        thermal_score = 1.0
    else:
        thermal_score = 0.0

    # ---------------------------------------------------------
    # Combined PFZ score
    #
    # Chlorophyll: 70%
    # Thermal front: 30%
    # ---------------------------------------------------------

    score = (
        chlorophyll_score * 0.70
        + thermal_score * 0.30
    )

    score = max(
        0.0,
        min(1.0, score),
    )

    # ---------------------------------------------------------
    # Classification
    # ---------------------------------------------------------

    if score >= 0.75:
        classification = "HIGH"

    elif score >= 0.45:
        classification = "MODERATE"

    else:
        classification = "LOW"

    return {
        "status": "success",
        "pfz_suitability_score": round(
            score,
            4,
        ),
        "classification": classification,
        "chlorophyll_mg_m3": (
            chlorophyll_mg_m3
        ),
        "chlorophyll_level": (
            chlorophyll_level
        ),
        "chlorophyll_score": round(
            chlorophyll_score,
            4,
        ),
        "thermal_front_detected": (
            thermal_front_detected
        ),
        "thermal_gradient_c_per_km": (
            thermal_gradient_c_per_km
        ),
        "thermal_front_score": (
            thermal_score
        ),
    }


OCEAN_TOOLS = [
    get_sst_data,
    get_chlorophyll_data,
    detect_thermal_front,
    calculate_pfz_suitability,
]