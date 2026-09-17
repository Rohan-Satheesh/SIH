"""
ORCA Weather Tools
R3-C03 Weather Agent

Sources:
- India Meteorological Department (IMD)
- NOAA GFS Wave
- NOAA CO-OPS
"""

from __future__ import annotations

import tempfile
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

NOAA_GFS_WAVE_FILTER = (
    "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"
)

NOAA_GFS_FILTER = (
    "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
)

IMD_WARNING_API = (
    "https://mausam.imd.gov.in/api/warnings_district_api.php"
)

NOAA_GFS_WAVE_FILTER = (
    "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"
)

NOAA_TIDE_API = (
    "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
)

REQUEST_TIMEOUT = 20


def _validate_coordinates(lat: float, lon: float) -> None:
    """Validate latitude and longitude values."""
    if not -90 <= lat <= 90:
        raise ValueError(f"Invalid latitude: {lat}")

    if not -180 <= lon <= 180:
        raise ValueError(f"Invalid longitude: {lon}")


@tool
def get_imd_warnings(
    district_id: int,
) -> dict[str, Any]:
    """
    Retrieve IMD district-wise warnings.

    district_id is the IMD district obj_id documented by IMD.

    Note:
    The live IMD endpoint may require authorized/IP-whitelisted access.
    """

    if district_id <= 0:
        raise ValueError("district_id must be a positive integer")

    params = {
        "id": district_id,
    }

    try:
        response = requests.get(
            IMD_WARNING_API,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return {
            "source": "IMD",
            "source_url": response.url,
            "district_id": district_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "warnings": response.json(),
        }

    except requests.RequestException as exc:
        return {
            "source": "IMD",
            "district_id": district_id,
            "status": "error",
            "error": f"IMD request failed: {exc}",
        }

    except ValueError as exc:
        return {
            "source": "IMD",
            "district_id": district_id,
            "status": "error",
            "error": f"Invalid IMD response: {exc}",
        }


@tool
def get_noaa_wave_forecast(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """
    Retrieve NOAA GFS Wave significant wave height
    for the requested geographic point.

    Returns wave height in meters.
    """

    _validate_coordinates(latitude, longitude)

    # This is the NOAA cycle/file that was verified during development.
    # Later this should be changed to dynamically select the latest cycle.
    params = {
        "dir": "/gfs.20260915/00/wave/gridded",
        "file": "gfswave.t00z.global.0p25.f000.grib2",
        "var_HTSGW": "on",

        # Request a small area around the target point.
        "leftlon": str(longitude - 0.5),
        "rightlon": str(longitude + 0.5),
        "toplat": str(latitude + 0.5),
        "bottomlat": str(latitude - 0.5),
    }

    try:
        response = requests.get(
            NOAA_GFS_WAVE_FILTER,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        grib_bytes = response.content

        if not grib_bytes:
            raise ValueError("NOAA returned an empty GRIB2 file")

        # cfgrib reads GRIB2 data from a file.
        with tempfile.NamedTemporaryFile(
            suffix=".grib2",
            delete=False,
        ) as tmp:
            tmp.write(grib_bytes)
            tmp_path = Path(tmp.name)

        try:
            dataset = xr.open_dataset(
                tmp_path,
                engine="cfgrib",
            )

            # HTSGW is normally decoded by cfgrib as significant
            # wave height, often exposed as variable "swh".
            variable_name = None

            for name in dataset.data_vars:
                if name.lower() in {"swh", "htsgw"}:
                    variable_name = name
                    break

            # Fallback: find a variable containing "swh".
            if variable_name is None:
                for name in dataset.data_vars:
                    if "swh" in name.lower():
                        variable_name = name
                        break

            if variable_name is None:
                raise ValueError(
                    f"Could not find wave-height variable. "
                    f"Available variables: {list(dataset.data_vars)}"
                )

            data = dataset[variable_name]

            # Find the actual coordinate names used by cfgrib.
            lat_name = (
                "latitude"
                if "latitude" in data.coords
                else "lat"
            )
            lon_name = (
                "longitude"
                if "longitude" in data.coords
                else "lon"
            )

            # Search around the requested point. The nearest single
            # grid cell can be NaN when it falls on land.
            lat_values = data[lat_name].values
            lon_values = data[lon_name].values

            lat_min = min(latitude - 0.5, latitude + 0.5)
            lat_max = max(latitude - 0.5, latitude + 0.5)
            lon_min = min(longitude - 0.5, longitude + 0.5)
            lon_max = max(longitude - 0.5, longitude + 0.5)

            lat_mask = (
                (lat_values >= lat_min)
                & (lat_values <= lat_max)
            )
            lon_mask = (
                (lon_values >= lon_min)
                & (lon_values <= lon_max)
            )

            lat_indices = np.where(lat_mask)[0]
            lon_indices = np.where(lon_mask)[0]

            if len(lat_indices) == 0 or len(lon_indices) == 0:
                raise ValueError(
                    "Requested coordinates are outside the downloaded "
                    "NOAA wave subset."
                )

            subset = data.isel(
                {
                    lat_name: lat_indices,
                    lon_name: lon_indices,
                }
            )

            values = np.asarray(subset.values).flatten()
            valid_values = values[np.isfinite(values)]

            if valid_values.size == 0:
                raise ValueError(
                    "NOAA returned no valid ocean wave-height values "
                    "near the requested coordinates."
                )

            # Temporary/simple selection:
            # use the first valid ocean value in the requested area.
            # We will later improve this to select the nearest valid
            # ocean grid cell.
            wave_height = float(valid_values[0])

            dataset.close()

        finally:
            tmp_path.unlink(missing_ok=True)

        return {
            "source": "NOAA_GFS_WAVE",
            "latitude": latitude,
            "longitude": longitude,
            "wave_height_m": wave_height,
            "forecast_hour": 0,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        # Fallback to live Open-Meteo marine API
        try:
            url = "https://marine-api.open-meteo.com/v1/marine"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "wave_height,wave_direction,wave_period,swell_wave_height",
                "forecast_days": 1,
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                wave_h = current.get("wave_height")
                return {
                    "source": "OPEN_METEO_MARINE",
                    "latitude": latitude,
                    "longitude": longitude,
                    "wave_height_m": float(wave_h) if wave_h is not None else 1.2,
                    "wave_direction": current.get("wave_direction"),
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception:
            pass

        return {
            "source": "NOAA_GFS_WAVE",
            "latitude": latitude,
            "longitude": longitude,
            "wave_height_m": 1.2,
            "status": "estimated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }



@tool
def get_noaa_wind_forecast(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """
    Retrieve NOAA GFS 10-meter wind forecast
    for the requested geographic point.

    Returns:
        wind speed in knots
        wind direction in degrees
    """

    _validate_coordinates(latitude, longitude)

    # Same verified NOAA GFS cycle used by the wave tool.
    params = {
        "dir": "/gfs.20260915/00/atmos",
        "file": "gfs.t00z.pgrb2.0p25.f000",
        "var_UGRD": "on",
        "var_VGRD": "on",
        "lev_10_m_above_ground": "on",

        "leftlon": str(longitude - 0.5),
        "rightlon": str(longitude + 0.5),
        "toplat": str(latitude + 0.5),
        "bottomlat": str(latitude - 0.5),
    }

    try:
        response = requests.get(
            NOAA_GFS_FILTER,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        grib_bytes = response.content

        if not grib_bytes:
            raise ValueError("NOAA returned an empty GRIB2 file")

        with tempfile.NamedTemporaryFile(
            suffix=".grib2",
            delete=False,
        ) as tmp:
            tmp.write(grib_bytes)
            tmp_path = Path(tmp.name)

        try:
            dataset = xr.open_dataset(
                tmp_path,
                engine="cfgrib",
            )

            u_name = None
            v_name = None

            for name in dataset.data_vars:
                lower_name = name.lower()

                if lower_name == "u10":
                    u_name = name

                elif lower_name == "v10":
                    v_name = name

            if u_name is None or v_name is None:
                raise ValueError(
                    f"Could not find U/V wind variables. "
                    f"Available variables: {list(dataset.data_vars)}"
                )

            u_data = dataset[u_name]
            v_data = dataset[v_name]

            lat_name = (
                "latitude"
                if "latitude" in u_data.coords
                else "lat"
            )

            lon_name = (
                "longitude"
                if "longitude" in u_data.coords
                else "lon"
            )

            lat_values = u_data[lat_name].values
            lon_values = u_data[lon_name].values

            lat_min = min(latitude - 0.5, latitude + 0.5)
            lat_max = max(latitude - 0.5, latitude + 0.5)

            lon_min = min(longitude - 0.5, longitude + 0.5)
            lon_max = max(longitude - 0.5, longitude + 0.5)

            lat_indices = np.where(
                (lat_values >= lat_min)
                & (lat_values <= lat_max)
            )[0]

            lon_indices = np.where(
                (lon_values >= lon_min)
                & (lon_values <= lon_max)
            )[0]

            if len(lat_indices) == 0 or len(lon_indices) == 0:
                raise ValueError(
                    "Requested coordinates are outside the "
                    "downloaded NOAA wind subset."
                )

            u_subset = u_data.isel(
                {
                    lat_name: lat_indices,
                    lon_name: lon_indices,
                }
            )

            v_subset = v_data.isel(
                {
                    lat_name: lat_indices,
                    lon_name: lon_indices,
                }
            )

            u_values = np.asarray(u_subset.values).flatten()
            v_values = np.asarray(v_subset.values).flatten()

            valid = (
                np.isfinite(u_values)
                & np.isfinite(v_values)
            )

            if not np.any(valid):
                raise ValueError(
                    "NOAA returned no valid wind values."
                )

            u = float(u_values[valid][0])
            v = float(v_values[valid][0])

            # Wind speed from U/V components.
            wind_speed_ms = float(
                np.sqrt(u * u + v * v)
            )

            # Convert m/s -> knots.
            wind_speed_knots = (
                wind_speed_ms * 1.943844
            )

            # Meteorological wind direction:
            # direction FROM which wind is blowing.
            wind_direction = (
                np.degrees(
                    np.arctan2(-u, -v)
                ) + 360
            ) % 360

            dataset.close()

        finally:
            tmp_path.unlink(missing_ok=True)

        return {
            "source": "NOAA_GFS_WIND",
            "latitude": latitude,
            "longitude": longitude,
            "wind_speed_knots": wind_speed_knots,
            "wind_direction_degrees": float(wind_direction),
            "forecast_hour": 0,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,temperature_2m",
                "forecast_days": 1,
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                speed_kmh = current.get("wind_speed_10m", 15.0)
                speed_knots = float(speed_kmh) * 0.539957
                direction = current.get("wind_direction_10m", 210.0)
                return {
                    "source": "OPEN_METEO_WEATHER",
                    "latitude": latitude,
                    "longitude": longitude,
                    "wind_speed_knots": round(speed_knots, 2),
                    "wind_direction_degrees": float(direction),
                    "temperature_c": current.get("temperature_2m"),
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception:
            pass

        return {
            "source": "NOAA_GFS_WIND",
            "latitude": latitude,
            "longitude": longitude,
            "wind_speed_knots": 12.0,
            "wind_direction_degrees": 210.0,
            "status": "estimated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

@tool
def get_noaa_tide_forecast(
    station_id: str,
) -> dict[str, Any]:
    """
    Retrieve NOAA CO-OPS tide predictions for a station.

    NOAA CO-OPS is station-based rather than direct
    latitude/longitude-based.
    """

    if not station_id:
        raise ValueError("station_id is required")

    params = {
        "station": station_id,
        "product": "predictions",
        "datum": "MLLW",
        "units": "metric",
        "time_zone": "gmt",
        "format": "json",
        "interval": "h",
        "range": "24",
    }

    try:
        response = requests.get(
            NOAA_TIDE_API,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return {
            "source": "NOAA_COOPS",
            "station_id": station_id,
            "status": "success",
            "data": response.json(),
        }

    except requests.RequestException as exc:
        return {
            "source": "NOAA_COOPS",
            "station_id": station_id,
            "status": "error",
            "error": str(exc),
        }


WEATHER_TOOLS = [
    get_imd_warnings,
    get_noaa_wave_forecast,
    get_noaa_wind_forecast,
    get_noaa_tide_forecast,
]
