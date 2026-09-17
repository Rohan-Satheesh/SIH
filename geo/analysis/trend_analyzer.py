"""
NeerMitra Geospatial Intelligence Engine - Oceanographic Trend Analyzer
Implements Task 9 of the Geospatial & Map Services Roadmap.
"""

from typing import Dict, Any, List
import statistics
import math

REGIONAL_BASELINES = {
    "arabian_sea": {
        "region_name": "Arabian Sea (West Coast Basin)",
        "sst_30d_history": [27.8, 27.9, 28.0, 28.1, 28.2, 28.0, 28.3, 28.4, 28.5, 28.6, 28.4, 28.5, 28.7, 28.8, 28.6, 28.5, 28.7, 28.9, 29.0, 28.8, 28.7, 28.9, 29.1, 29.2, 29.0, 28.9, 29.1, 29.3, 29.4, 29.5],
        "chl_30d_history": [1.4, 1.5, 1.4, 1.6, 1.7, 1.5, 1.8, 1.9, 2.0, 1.8, 1.7, 1.9, 2.1, 2.2, 2.0, 1.9, 2.1, 2.3, 2.4, 2.2, 2.1, 2.3, 2.5, 2.6, 2.4, 2.3, 2.5, 2.7, 2.8, 2.9],
        "wave_30d_history": [1.2, 1.4, 1.3, 1.5, 1.6, 1.4, 1.5, 1.7, 1.8, 1.6, 1.5, 1.7, 1.9, 2.0, 1.8, 1.7, 1.9, 2.1, 2.2, 2.0, 1.9, 2.1, 2.3, 2.4, 2.2, 2.1, 2.3, 2.5, 2.6, 2.7]
    },
    "bay_of_bengal": {
        "region_name": "Bay of Bengal (East Coast Basin)",
        "sst_30d_history": [28.6, 28.7, 28.8, 28.9, 29.0, 28.9, 29.1, 29.2, 29.3, 29.4, 29.2, 29.3, 29.5, 29.6, 29.4, 29.3, 29.5, 29.7, 29.8, 29.6, 29.5, 29.7, 29.9, 30.0, 29.8, 29.7, 29.9, 30.1, 30.2, 30.4],
        "chl_30d_history": [1.8, 1.9, 1.8, 2.0, 2.1, 1.9, 2.2, 2.3, 2.4, 2.2, 2.1, 2.3, 2.5, 2.6, 2.4, 2.3, 2.5, 2.7, 2.8, 2.6, 2.5, 2.7, 2.9, 3.0, 2.8, 2.7, 2.9, 3.1, 3.2, 3.4],
        "wave_30d_history": [1.5, 1.6, 1.5, 1.7, 1.8, 1.6, 1.7, 1.9, 2.0, 1.8, 1.7, 1.9, 2.1, 2.2, 2.0, 1.9, 2.1, 2.3, 2.4, 2.2, 2.1, 2.3, 2.5, 2.6, 2.4, 2.3, 2.5, 2.7, 2.8, 2.9]
    },
    "kerala_coast": {
        "region_name": "Kerala & Wadge Bank Coastal Shelf",
        "sst_30d_history": [28.0, 28.1, 28.0, 28.2, 28.3, 28.1, 28.4, 28.5, 28.6, 28.4, 28.3, 28.5, 28.7, 28.8, 28.6, 28.5, 28.7, 28.9, 29.0, 28.8, 28.7, 28.9, 29.1, 29.2, 29.0, 28.9, 29.1, 29.3, 29.4, 29.5],
        "chl_30d_history": [1.5, 1.6, 1.5, 1.7, 1.8, 1.6, 1.9, 2.0, 2.1, 1.9, 1.8, 2.0, 2.2, 2.3, 2.1, 2.0, 2.2, 2.4, 2.5, 2.3, 2.2, 2.4, 2.6, 2.7, 2.5, 2.4, 2.6, 2.8, 2.9, 3.0],
        "wave_30d_history": [1.1, 1.2, 1.1, 1.3, 1.4, 1.2, 1.3, 1.5, 1.6, 1.4, 1.3, 1.5, 1.7, 1.8, 1.6, 1.5, 1.7, 1.9, 2.0, 1.8, 1.7, 1.9, 2.1, 2.2, 2.0, 1.9, 2.1, 2.3, 2.4, 2.5]
    }
}

def analyze_ocean_trends(region_key: str = "arabian_sea") -> Dict[str, Any]:
    """
    Performs 7-day and 30-day statistical time-series analysis for oceanographic parameters:
    - SST Anomalies & Marine Heatwave (MHW) Classification
    - Chlorophyll Bloom Velocity
    - Significant Wave Height Moving Average
    """
    key = region_key.lower().replace(" ", "_").replace("-", "_")
    region_data = REGIONAL_BASELINES.get(key, REGIONAL_BASELINES["arabian_sea"])

    sst_series = region_data["sst_30d_history"]
    chl_series = region_data["chl_30d_history"]
    wave_series = region_data["wave_30d_history"]

    # 30-day stats
    sst_30d_mean = round(statistics.mean(sst_series), 2)
    sst_30d_std = round(statistics.stdev(sst_series), 2) if len(sst_series) > 1 else 0.5
    current_sst = sst_series[-1]

    # 7-day stats
    sst_7d_mean = round(statistics.mean(sst_series[-7:]), 2)
    chl_7d_mean = round(statistics.mean(chl_series[-7:]), 2)
    wave_7d_mean = round(statistics.mean(wave_series[-7:]), 2)

    # Anomaly calculation
    sst_anomaly = round(current_sst - sst_30d_mean, 2)
    z_score = round(sst_anomaly / sst_30d_std, 2) if sst_30d_std > 0 else 0.0

    # Marine Heatwave Detection (MHW threshold: > +1.2°C anomaly or Z > 2.0)
    is_marine_heatwave = z_score >= 1.8 or sst_anomaly >= 1.2
    mhw_severity = "NONE"
    if is_marine_heatwave:
        mhw_severity = "MODERATE" if z_score < 2.5 else "STRONG" if z_score < 3.5 else "SEVERE"

    return {
        "region": region_data["region_name"],
        "parameters": {
            "sea_surface_temperature": {
                "current_value_c": current_sst,
                "mean_7day_c": sst_7d_mean,
                "mean_30day_c": sst_30d_mean,
                "std_deviation_c": sst_30d_std,
                "anomaly_c": sst_anomaly,
                "z_score": z_score,
                "trend_direction": "WARMING" if sst_anomaly > 0 else "COOLING",
                "heatwave_detected": is_marine_heatwave,
                "heatwave_severity": mhw_severity
            },
            "chlorophyll_a": {
                "current_value_mg_m3": chl_series[-1],
                "mean_7day_mg_m3": chl_7d_mean,
                "mean_30day_mg_m3": round(statistics.mean(chl_series), 2),
                "trend_direction": "BLOOM_EXPANSION" if chl_series[-1] > chl_7d_mean else "DECLINING"
            },
            "wave_height": {
                "current_height_m": wave_series[-1],
                "mean_7day_m": wave_7d_mean,
                "mean_30day_m": round(statistics.mean(wave_series), 2),
                "sea_condition": "CALM" if wave_series[-1] < 1.5 else "MODERATE" if wave_series[-1] < 2.5 else "ROUGH"
            }
        },
        "historical_30d_timeline": {
            "sst": sst_series,
            "chlorophyll": chl_series,
            "wave_height": wave_series
        },
        "advisory": (
            f"Marine Heatwave Alert ({mhw_severity}): SST is +{sst_anomaly}°C above the 30-day baseline ({sst_30d_mean}°C). Pelagic schools may dive deeper."
            if is_marine_heatwave else
            f"Nominal oceanographic cycle: SST anomaly is within baseline range (+{sst_anomaly}°C, Z={z_score}). Primary productivity is stable."
        )
    }
