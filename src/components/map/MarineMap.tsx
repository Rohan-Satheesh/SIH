import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import ScanEffect from '@/components/hud/ScanEffect';
import ProvenanceModal from '@/components/hud/ProvenanceModal';
import { Layers, ShieldCheck, Info, RefreshCw, ChevronDown, ChevronUp, Compass, Navigation, MapPin, Anchor } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiUrl } from '@/services/api';
import { 
  getSelectedLocation, 
  setSelectedLocation, 
  getNearestCoastalSector 
} from '@/services/liveMarineService';

// Fix Leaflet's default icon path issues
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

function isValidGeoJson(data: any): boolean {
  if (!data || typeof data !== 'object') return false;
  if (data.detail || data.error || (data.message && !data.type)) return false;
  if (data.type === 'FeatureCollection') {
    return Array.isArray(data.features);
  }
  if (data.type === 'Feature') {
    return !!data.geometry && typeof data.geometry === 'object';
  }
  const validTypes = ['Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon', 'GeometryCollection'];
  return typeof data.type === 'string' && validTypes.includes(data.type);
}

interface SpatialLayerMeta {
  layer_name: string;
  display_name: string;
  geometry_type: string;
  feature_count: number;
}

export interface NavigationCourse {
  id: string;
  origin: {
    lat: number;
    lng: number;
    name: string;
  };
  destination: {
    lat: number;
    lng: number;
    name: string;
    confidence?: string;
    species?: string;
  };
  distance?: string;
  bearing?: string;
  fuelEstimate?: string;
  sst?: string;
  waypoints?: [number, number][];
}

interface MarineMapProps {
  isScanning?: boolean;
  onScanComplete?: () => void;
  center?: [number, number];
  zoom?: number;
  showSST?: boolean;
  showChlorophyll?: boolean;
  showVessels?: boolean;
  showPFZ?: boolean;
  showGeofence?: boolean;
  initialPinLabel?: string;
  course?: NavigationCourse | null;
  onClearCourse?: () => void;
}

interface AISVessel {
  mmsi?: string | number;
  imo?: string | number;
  name: string;
  latitude: number;
  longitude: number;
  heading?: number;
  speed?: number;
  course?: number;
  ship_type?: string;
  last_position?: string;
}

const CARTO_API_KEY = import.meta.env.VITE_CARTO_API_KEY || 'cb1_2m04_1_3f470e2298f7bf1f28a78ef9';

const CARTO_DARK_BASEMAP = {
  id: 'carto-dark',
  name: 'CARTO Dark Matter',
  url: CARTO_API_KEY
    ? `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`
    : 'https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png',
  subdomains: 'abcd',
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
};

const LAYER_COLORS: Record<string, { color: string; fillColor: string }> = {
  india_eez_boundaries: { color: '#00D2FF', fillColor: '#00D2FF' },
  india_marine_protected_areas: { color: '#f43f5e', fillColor: '#f43f5e' },
  india_coastal_fishing_sectors: { color: '#10b981', fillColor: '#10b981' },
  sst_thermal_fronts: { color: '#f59e0b', fillColor: '#f59e0b' },
  chlorophyll_blooms: { color: '#10b981', fillColor: '#10b981' },
  composite_risk_grid: { color: '#ec4899', fillColor: '#ec4899' },
  international_boundaries: { color: '#818cf8', fillColor: '#818cf8' },
};

const DEFAULT_SPATIAL_LAYERS: SpatialLayerMeta[] = [
  {
    layer_name: 'india_eez_boundaries',
    display_name: 'India EEZ Boundaries',
    geometry_type: 'MultiPolygon',
    feature_count: 1
  },
  {
    layer_name: 'india_marine_protected_areas',
    display_name: 'Marine Protected Areas (MPA)',
    geometry_type: 'MultiPolygon',
    feature_count: 5
  },
  {
    layer_name: 'india_coastal_fishing_sectors',
    display_name: 'State Fishing Sectors',
    geometry_type: 'MultiPolygon',
    feature_count: 7
  },
  {
    layer_name: 'sst_thermal_fronts',
    display_name: 'SST Thermal Fronts',
    geometry_type: 'Polygon',
    feature_count: 4
  },
  {
    layer_name: 'chlorophyll_blooms',
    display_name: 'Chlorophyll-a Bio-Plumes',
    geometry_type: 'Polygon',
    feature_count: 3
  },
  {
    layer_name: 'composite_risk_grid',
    display_name: 'Composite Risk Grid',
    geometry_type: 'Polygon',
    feature_count: 168
  }
];

// Strict Geographic Bounds for India & Surrounding Waters (Arabian Sea, Bay of Bengal, Indian Ocean, Andaman & Lakshadweep)
const INDIA_BOUNDS: L.LatLngBoundsExpression = [
  [-2.0, 58.0],  // South-West corner (Equatorial Indian Ocean)
  [38.5, 102.0], // North-East corner (Northern Borders & Andaman Sea)
];

// Pinpoint icon generator displaying custom pin, pulsing radar ring, and floating coordinate badge
const createPinpointIcon = (label: string, lat: number, lng: number) => {
  return L.divIcon({
    className: 'custom-marine-pinpoint',
    html: `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%); pointer-events: auto; cursor: pointer;">
        <!-- Top Coordinate Badge -->
        <div style="background: rgba(7, 17, 31, 0.96); backdrop-filter: blur(8px); border: 1.5px solid #22d3ee; color: #fff; padding: 4px 10px; border-radius: 8px; box-shadow: 0 4px 18px rgba(0,0,0,0.85); margin-bottom: 4px; display: flex; flex-direction: column; align-items: center; white-space: nowrap;">
          <div style="font-size: 11px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 5px;">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #38bdf8; box-shadow: 0 0 6px #38bdf8;"></span>
            ${label}
          </div>
          <div style="font-size: 10px; font-family: monospace; font-weight: 600; color: #f8fafc; margin-top: 1px;">
            ${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E
          </div>
        </div>

        <!-- Pin SVG -->
        <div style="position: relative; width: 28px; height: 36px;">
          <svg viewBox="0 0 24 32" width="28" height="36" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 4px 10px rgba(0,0,0,0.9));">
            <path d="M12 0C5.37 0 0 5.37 0 12C0 21.5 12 32 12 32C12 32 24 21.5 24 12C24 5.37 18.63 0 12 0Z" fill="#0891b2" stroke="#22d3ee" stroke-width="1.8"/>
            <circle cx="12" cy="12" r="5" fill="#ffffff"/>
            <circle cx="12" cy="12" r="2.8" fill="#0e7490"/>
          </svg>
        </div>

        <!-- Ground Sonar Ping -->
        <div style="position: absolute; bottom: -5px; width: 22px; height: 8px; border-radius: 50%; background: rgba(34, 211, 238, 0.4); border: 1.5px solid #22d3ee;"></div>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
    popupAnchor: [0, -45],
  });
};

const createOriginIcon = (label: string, lat: number, lng: number) => {
  return L.divIcon({
    className: 'custom-marine-origin',
    html: `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%); pointer-events: auto; cursor: pointer;">
        <div style="background: rgba(11, 57, 84, 0.95); backdrop-filter: blur(8px); border: 1.5px solid #10b981; color: #fff; padding: 4px 10px; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.6); margin-bottom: 4px; display: flex; flex-direction: column; align-items: center; white-space: nowrap;">
          <div style="font-size: 11px; font-weight: 700; color: #34d399; display: flex; align-items: center; gap: 5px;">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></span>
            ⚓ Departure: ${label}
          </div>
          <div style="font-size: 9.5px; font-family: monospace; font-weight: 600; color: #e2e8f0; margin-top: 1px;">
            ${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E
          </div>
        </div>
        <div style="position: relative; width: 28px; height: 36px;">
          <svg viewBox="0 0 24 32" width="28" height="36" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 4px 10px rgba(0,0,0,0.8));">
            <path d="M12 0C5.37 0 0 5.37 0 12C0 21.5 12 32 12 32C12 32 24 21.5 24 12C24 5.37 18.63 0 12 0Z" fill="#059669" stroke="#34d399" stroke-width="1.8"/>
            <circle cx="12" cy="12" r="5" fill="#ffffff"/>
            <circle cx="12" cy="12" r="2.8" fill="#047857"/>
          </svg>
        </div>
        <div style="position: absolute; bottom: -5px; width: 20px; height: 8px; border-radius: 50%; background: rgba(16, 185, 129, 0.4); border: 1.5px solid #10b981;"></div>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
    popupAnchor: [0, -45],
  });
};

const createDestinationIcon = (label: string, lat: number, lng: number, distance?: string, bearing?: string) => {
  return L.divIcon({
    className: 'custom-marine-destination',
    html: `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%); pointer-events: auto; cursor: pointer;">
        <div style="background: rgba(11, 57, 84, 0.95); backdrop-filter: blur(8px); border: 1.5px solid #f59e0b; color: #fff; padding: 4px 10px; border-radius: 8px; box-shadow: 0 4px 18px rgba(0,0,0,0.7); margin-bottom: 4px; display: flex; flex-direction: column; align-items: center; white-space: nowrap;">
          <div style="font-size: 11px; font-weight: 700; color: #fbbf24; display: flex; align-items: center; gap: 5px;">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #f59e0b; box-shadow: 0 0 8px #f59e0b;"></span>
            🎯 Target PFZ: ${label}
          </div>
          ${distance ? `<div style="font-size: 10px; font-weight: 600; color: #38bdf8; margin-top: 1px;">${distance} • ${bearing || ''}</div>` : ''}
        </div>
        <div style="position: relative; width: 32px; height: 40px;">
          <svg viewBox="0 0 24 32" width="32" height="40" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 4px 12px rgba(245, 158, 11, 0.6));">
            <path d="M12 0C5.37 0 0 5.37 0 12C0 21.5 12 32 12 32C12 32 24 21.5 24 12C24 5.37 18.63 0 12 0Z" fill="#d97706" stroke="#fbbf24" stroke-width="2"/>
            <circle cx="12" cy="12" r="5" fill="#ffffff"/>
            <circle cx="12" cy="12" r="2.8" fill="#b45309"/>
          </svg>
        </div>
        <div style="position: absolute; bottom: -6px; width: 28px; height: 10px; border-radius: 50%; background: rgba(245, 158, 11, 0.35); border: 1.5px solid #f59e0b;"></div>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
    popupAnchor: [0, -50],
  });
};

function CourseCameraController({ course }: { course?: NavigationCourse | null }) {
  const map = useMap();

  useEffect(() => {
    if (course?.origin && course?.destination) {
      const bounds = L.latLngBounds(
        [course.origin.lat, course.origin.lng],
        [course.destination.lat, course.destination.lng]
      );
      map.fitBounds(bounds, {
        padding: [70, 70],
        maxZoom: 11,
        animate: true
      });
    }
  }, [course, map]);

  useEffect(() => {
    const handleFitBounds = () => {
      if (course?.origin && course?.destination) {
        const bounds = L.latLngBounds(
          [course.origin.lat, course.origin.lng],
          [course.destination.lat, course.destination.lng]
        );
        map.fitBounds(bounds, {
          padding: [70, 70],
          maxZoom: 11,
          animate: true
        });
      }
    };
    window.addEventListener('marine:fit-course-bounds', handleFitBounds);
    return () => window.removeEventListener('marine:fit-course-bounds', handleFitBounds);
  }, [course, map]);

  return null;
}

function MapCameraController({ 
  center,
  zoom,
  onSectorChange 
}: { 
  center?: [number, number];
  zoom?: number;
  onSectorChange: (pin: { lat: number; lng: number; label: string }) => void 
}) {
  const map = useMap();

  useEffect(() => {
    if (center && (center[0] !== 15.0 || center[1] !== 78.5)) {
      map.flyTo(center, zoom || 8, { duration: 1.2 });
    }
  }, [center?.[0], center?.[1], zoom, map]);

  useEffect(() => {
    const handleSectorChange = (e: any) => {
      const { lat, lng, name, fromMapClick } = e.detail || {};
      if (typeof lat === 'number' && typeof lng === 'number') {
        if (!fromMapClick) {
          map.flyTo([lat, lng], 8, { duration: 1.5 });
        }
        onSectorChange({
          lat,
          lng,
          label: name || `${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E`
        });
      }
    };
    window.addEventListener('marine:sector-change', handleSectorChange);
    return () => window.removeEventListener('marine:sector-change', handleSectorChange);
  }, [map, onSectorChange]);
  return null;
}

function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    }
  });
  return null;
}

export default function MarineMap({
  isScanning = false,
  onScanComplete,
  center = [15.0, 78.5],
  zoom = 5,
  showSST = false,
  showChlorophyll = false,
  showVessels = true,
  initialPinLabel,
  course = null,
  onClearCourse,
}: MarineMapProps) {
  const [selectedPinpoint, setSelectedPinpoint] = useState<{
    lat: number;
    lng: number;
    label: string;
  } | null>(() => {
    if (center && (center[0] !== 15.0 || center[1] !== 78.5)) {
      return {
        lat: center[0],
        lng: center[1],
        label: initialPinLabel || `${center[0].toFixed(4)}°N, ${center[1].toFixed(4)}°E`
      };
    }
    const loc = getSelectedLocation();
    return {
      lat: loc.lat,
      lng: loc.lng,
      label: loc.name
    };
  });

  useEffect(() => {
    if (center && (center[0] !== 15.0 || center[1] !== 78.5)) {
      setSelectedPinpoint(prev => ({
        lat: center[0],
        lng: center[1],
        label: initialPinLabel || prev?.label || `${center[0].toFixed(4)}°N, ${center[1].toFixed(4)}°E`
      }));
    }
  }, [center?.[0], center?.[1], initialPinLabel]);

  const handleMapClick = (lat: number, lng: number) => {
    const { sector, distanceKm } = getNearestCoastalSector(lat, lng);
    const label = distanceKm > 20 
      ? `Target (${distanceKm}km off ${sector.name.split(' ')[0]})`
      : `${sector.name} (${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E)`;
    setSelectedPinpoint({ lat, lng, label });
    setSelectedLocation({ lat, lng, name: label });
    window.dispatchEvent(new CustomEvent('marine:sector-change', {
      detail: { lat, lng, name: label, fromMapClick: true }
    }));
  };

  const [spatialLayers, setSpatialLayers] = useState<SpatialLayerMeta[]>(DEFAULT_SPATIAL_LAYERS);
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    DEFAULT_SPATIAL_LAYERS.forEach(l => {
      initial[l.layer_name] = !l.layer_name.includes('grid');
    });
    if (showSST) initial['sst_thermal_fronts'] = true;
    if (showChlorophyll) initial['chlorophyll_blooms'] = true;
    return initial;
  });
  const [layerData, setLayerData] = useState<Record<string, any>>({});
  const [loadingLayers, setLoadingLayers] = useState<Record<string, boolean>>({});
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [whyModalOpen, setWhyModalOpen] = useState(false);
  const [selectedItemForWhy, setSelectedItemForWhy] = useState<string>('');
  const [isLayersCollapsed, setIsLayersCollapsed] = useState(false);
  const [vessels, setVessels] = useState<AISVessel[]>([]);
  const [aisConnected, setAisConnected] = useState(false);

  useEffect(() => {
    if (!showVessels) return;

    const fetchVessels = () => {
      fetch(apiUrl('/api/ais/vessels'))
        .then(response => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then(data => {
          setAisConnected(data.connected === true);
          setVessels(Array.isArray(data.vessels) ? data.vessels : []);
        })
        .catch(() => {
          setAisConnected(false);
          setVessels([]);
        });
    };

    fetchVessels();
    const interval = setInterval(fetchVessels, 60000);
    return () => clearInterval(interval);
  }, [showVessels]);

  // 1. Fetch live feature counts and dynamic layers from backend
  useEffect(() => {
    fetch(apiUrl('/api/spatial/layers'))
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        const layersList = Array.isArray(data) ? data : Array.isArray(data?.layers) ? data.layers : typeof data === 'object' ? Object.values(data) : [];
        if (layersList.length > 0) {
          const coreLayers: SpatialLayerMeta[] = [...layersList];
          // Ensure ocean layers are appended
          const extraLayers = DEFAULT_SPATIAL_LAYERS.slice(3);
          extraLayers.forEach(extra => {
            if (!coreLayers.some(l => l.layer_name === extra.layer_name)) {
              coreLayers.push(extra);
            }
          });
          setSpatialLayers(coreLayers);
        }
      })
      .catch(() => {
        // Keeps DEFAULT_SPATIAL_LAYERS seamlessly
      });
  }, []);

  // 2. Fetch GeoJSON for active layers
  useEffect(() => {
    spatialLayers.forEach(layer => {
      const isEnabled = activeLayers[layer.layer_name];
      if (isEnabled && !layerData[layer.layer_name] && !loadingLayers[layer.layer_name]) {
        setLoadingLayers(prev => ({ ...prev, [layer.layer_name]: true }));
        
        let endpoint = apiUrl(`/api/spatial/layers/${layer.layer_name}`);
        if (layer.layer_name === 'sst_thermal_fronts') {
          endpoint = apiUrl('/api/geo/ocean-layers?layer_type=sst');
        } else if (layer.layer_name === 'chlorophyll_blooms') {
          endpoint = apiUrl('/api/geo/ocean-layers?layer_type=chlorophyll');
        } else if (layer.layer_name === 'composite_risk_grid') {
          endpoint = apiUrl('/api/geo/composite-risk-grid');
        }

        const fetchLayer = async () => {
          try {
            let res = await fetch(endpoint);
            if (!res.ok && endpoint.includes('/api/spatial/layers/')) {
              res = await fetch(apiUrl(`/api/geo/layer/${layer.layer_name}`));
            }
            if (!res.ok) {
              throw new Error(`HTTP ${res.status}`);
            }
            const geoJson = await res.json();
            if (isValidGeoJson(geoJson)) {
              setLayerData(prev => ({ ...prev, [layer.layer_name]: geoJson }));
            }
          } catch (err) {
            console.warn(`Layer data for ${layer.layer_name} could not be loaded:`, err);
          } finally {
            setLoadingLayers(prev => ({ ...prev, [layer.layer_name]: false }));
          }
        };

        fetchLayer();
      }
    });
  }, [activeLayers, spatialLayers, layerData, loadingLayers]);

  const toggleLayer = (layerName: string) => {
    setActiveLayers(prev => ({ ...prev, [layerName]: !prev[layerName] }));
  };

  const getStyleForLayer = (layerName: string, feature?: any) => {
    if (feature && feature.properties && feature.properties.color) {
      return {
        color: feature.properties.color,
        weight: 1.5,
        opacity: 0.9,
        fillColor: feature.properties.fillColor || feature.properties.color,
        fillOpacity: feature.properties.fillOpacity || 0.25,
      };
    }

    const palette = LAYER_COLORS[layerName] || { color: '#38bdf8', fillColor: '#38bdf8' };
    const isMPA = layerName.includes('protected');
    const isSector = layerName.includes('fishing');

    return {
      color: palette.color,
      weight: isMPA ? 2.5 : isSector ? 1.5 : 2,
      opacity: 0.9,
      fillColor: palette.fillColor,
      fillOpacity: isMPA ? 0.25 : isSector ? 0.12 : 0.04,
      dashArray: isMPA ? '4, 4' : layerName.includes('eez') ? '6, 8' : undefined,
    };
  };

  const onEachFeature = (feature: any, layer: L.Layer) => {
    layer.on({
      click: () => {
        setSelectedFeature(feature.properties);
      },
      mouseover: (e: any) => {
        const target = e.target;
        target.setStyle({
          weight: 3,
          fillOpacity: 0.4,
        });
      },
      mouseout: (e: any) => {
        const target = e.target;
        target.setStyle({
          weight: 2,
          fillOpacity: 0.15,
        });
      }
    });
  };

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#070D18] select-none">
      {/* Satellite Scan Animation Layer */}
      <ScanEffect isScanning={isScanning} onScanComplete={onScanComplete} />

      {/* Map Component */}
      <MapContainer
        center={center}
        zoom={zoom}
        minZoom={4.5}
        maxZoom={18}
        maxBounds={INDIA_BOUNDS}
        maxBoundsViscosity={1.0}
        style={{ height: '100%', width: '100%', background: '#070D18' }}
        zoomControl={false}
      >
        <MapCameraController center={center} zoom={zoom} onSectorChange={setSelectedPinpoint} />
        <CourseCameraController course={course} />
        <MapClickHandler onMapClick={handleMapClick} />

        {/* Active Marine Navigation Course Polylines & Waypoints */}
        {course && course.origin && course.destination && (
          <>
            {/* Outer Glowing Navigation Track Corridor */}
            <Polyline
              positions={[
                [course.origin.lat, course.origin.lng],
                ...(course.waypoints || []),
                [course.destination.lat, course.destination.lng]
              ]}
              pathOptions={{
                color: '#00D2FF',
                weight: 7,
                opacity: 0.35,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />

            {/* High-visibility Dashed Marine Navigation Track */}
            <Polyline
              positions={[
                [course.origin.lat, course.origin.lng],
                ...(course.waypoints || []),
                [course.destination.lat, course.destination.lng]
              ]}
              pathOptions={{
                color: '#00F0FF',
                weight: 3.5,
                opacity: 0.95,
                dashArray: '10, 10',
                lineCap: 'round',
                lineJoin: 'round'
              }}
            >
              <Popup>
                <div className="p-1 min-w-[190px] text-slate-100">
                  <div className="font-bold text-xs text-cyan-400 border-b border-slate-700/80 pb-1 mb-1">
                    🧭 Marine Navigation Course
                  </div>
                  <div className="text-[11px] font-mono space-y-1 text-slate-300">
                    <div>Departure: <strong className="text-emerald-400">{course.origin.name}</strong></div>
                    <div>Destination: <strong className="text-amber-400">{course.destination.name}</strong></div>
                    {course.distance && <div>Distance: <strong className="text-white">{course.distance}</strong></div>}
                    {course.bearing && <div>Bearing: <strong className="text-cyan-300">{course.bearing}</strong></div>}
                    {course.fuelEstimate && <div>Fuel Est: <strong className="text-yellow-400">{course.fuelEstimate}</strong></div>}
                  </div>
                </div>
              </Popup>
            </Polyline>

            {/* Origin Departure Marker */}
            <Marker
              position={[course.origin.lat, course.origin.lng]}
              icon={createOriginIcon(course.origin.name, course.origin.lat, course.origin.lng)}
              zIndexOffset={1000}
            >
              <Popup>
                <div className="p-1 min-w-[190px] text-slate-100">
                  <div className="font-bold text-xs text-emerald-400 flex items-center gap-1.5 border-b border-slate-700/80 pb-1 mb-1">
                    ⚓ Departure Point (Origin)
                  </div>
                  <div className="text-xs font-bold text-white">{course.origin.name}</div>
                  <div className="text-[11px] font-mono text-slate-400 mt-1">
                    {course.origin.lat.toFixed(4)}°N, {course.origin.lng.toFixed(4)}°E
                  </div>
                </div>
              </Popup>
            </Marker>

            {/* Target Destination Marker */}
            <Marker
              position={[course.destination.lat, course.destination.lng]}
              icon={createDestinationIcon(
                course.destination.name,
                course.destination.lat,
                course.destination.lng,
                course.distance,
                course.bearing
              )}
              zIndexOffset={1001}
            >
              <Popup>
                <div className="p-1 min-w-[200px] text-slate-100">
                  <div className="font-bold text-xs text-amber-400 flex items-center gap-1.5 border-b border-slate-700/80 pb-1 mb-1">
                    🎯 Target Potential Fishing Zone (PFZ)
                  </div>
                  <div className="text-xs font-bold text-white">{course.destination.name}</div>
                  {course.destination.species && (
                    <div className="text-[11px] text-emerald-400 font-medium mt-0.5">{course.destination.species}</div>
                  )}
                  <div className="text-[11px] font-mono space-y-0.5 text-slate-300 mt-1.5 pt-1.5 border-t border-slate-800">
                    <div>Coordinates: <span className="text-white">{course.destination.lat.toFixed(4)}°N, {course.destination.lng.toFixed(4)}°E</span></div>
                    {course.distance && <div>Distance: <span className="text-white">{course.distance}</span></div>}
                    {course.bearing && <div>Bearing: <span className="text-cyan-300">{course.bearing}</span></div>}
                    {course.fuelEstimate && <div>Fuel Est: <span className="text-yellow-400">{course.fuelEstimate}</span></div>}
                  </div>
                </div>
              </Popup>
            </Marker>
          </>
        )}

        {/* Active Selected Location Pinpoint Marker (shown when no course is plotted) */}
        {!course && selectedPinpoint && (
          <Marker
            position={[selectedPinpoint.lat, selectedPinpoint.lng]}
            icon={createPinpointIcon(selectedPinpoint.label, selectedPinpoint.lat, selectedPinpoint.lng)}
            zIndexOffset={1000}
          >
            <Popup>
              <div className="p-1 min-w-[190px] text-slate-100">
                <div className="font-bold text-xs text-cyan-400 flex items-center gap-1.5 border-b border-slate-700/80 pb-1.5 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                  {selectedPinpoint.label}
                </div>
                <div className="text-[11px] font-mono space-y-1 text-slate-300">
                  <div>
                    <span className="text-slate-500">Latitude:</span>{' '}
                    <strong className="text-white">{selectedPinpoint.lat.toFixed(4)}°N</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">Longitude:</span>{' '}
                    <strong className="text-white">{selectedPinpoint.lng.toFixed(4)}°E</strong>
                  </div>
                  <div className="text-[10px] text-cyan-400/90 pt-1 flex items-center gap-1">
                    <span>•</span> Monitored Marine Telemetry Active
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Permanent CARTO Dark Matter Basemap */}
        <TileLayer
          key={CARTO_DARK_BASEMAP.id}
          attribution={CARTO_DARK_BASEMAP.attribution}
          url={CARTO_DARK_BASEMAP.url}
          subdomains={CARTO_DARK_BASEMAP.subdomains}
          maxZoom={19}
        />

        {/* Dynamic PostGIS Spatial Boundary Layers */}
        {spatialLayers.map(layer => {
          const data = layerData[layer.layer_name];
          if (!activeLayers[layer.layer_name] || !isValidGeoJson(data)) return null;
          const count = Array.isArray(data.features) ? data.features.length : 1;
          return (
            <GeoJSON
              key={`${layer.layer_name}-${count}`}
              data={data}
              style={(feature) => getStyleForLayer(layer.layer_name, feature)}
              onEachFeature={onEachFeature}
            />
          );
        })}

        {showVessels && vessels.map((vessel, index) => (
          <Marker
            key={`${vessel.mmsi ?? vessel.imo ?? vessel.name}-${index}`}
            position={[vessel.latitude, vessel.longitude]}
          >
            <Popup>
              <strong>{vessel.name}</strong>
              <br />
              MMSI: {vessel.mmsi ?? 'Unavailable'}
              <br />
              Speed: {vessel.speed ?? 'Unavailable'}
              <br />
              Heading: {vessel.heading ?? 'Unavailable'}
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Floating HUD: PostGIS Layer Switcher (Collapsible) */}
      {isLayersCollapsed ? (
        <button
          onClick={() => setIsLayersCollapsed(false)}
          className="absolute top-3 right-10 z-[500] flex items-center space-x-2 px-3 py-2 bg-[#091120]/95 backdrop-blur-md border border-slate-800 hover:border-cyan-500/50 rounded-xl text-xs font-semibold text-white shadow-2xl transition-all cursor-pointer group"
          title="Open Spatial Layers Panel"
        >
          <div className="w-5 h-5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <Layers className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <span className="text-[11px] font-bold tracking-wide">Spatial Layers</span>
          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30">
            {Object.values(activeLayers).filter(Boolean).length}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-white transition-colors" />
        </button>
      ) : (
        <div className="absolute top-3 right-10 z-[500] bg-[#091120]/95 backdrop-blur-md border border-slate-800 rounded-xl p-3 shadow-2xl max-w-xs text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
            <div className="flex items-center space-x-1.5 text-cyan-400 font-bold">
              <Layers className="w-3.5 h-3.5" />
              <span className="uppercase tracking-wider text-[11px]">PostGIS Spatial Layers</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="text-[10px] font-mono text-emerald-400">PostgreSQL 15</span>
              <button
                onClick={() => setIsLayersCollapsed(true)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                title="Collapse Panel"
              >
                <ChevronUp className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {spatialLayers.length === 0 ? (
            <div className="text-[11px] text-slate-400 py-1">Connecting to PostGIS engine...</div>
          ) : (
            <div className="space-y-1.5 max-h-48 overflow-y-auto scrollbar-thin">
              {spatialLayers.map(layer => {
                const isActive = activeLayers[layer.layer_name];
                const palette = LAYER_COLORS[layer.layer_name] || { color: '#38bdf8' };
                const isLoading = loadingLayers[layer.layer_name];

                return (
                  <button
                    key={layer.layer_name}
                    onClick={() => toggleLayer(layer.layer_name)}
                    className={cn(
                      "w-full flex items-center justify-between p-2 rounded-lg border text-left transition-all cursor-pointer",
                      isActive 
                        ? "bg-slate-900 border-slate-700 text-white" 
                        : "bg-slate-950/60 border-slate-800/60 text-slate-500 hover:text-slate-300"
                    )}
                  >
                    <div className="flex items-center space-x-2">
                      <span 
                        className="w-2.5 h-2.5 rounded-full" 
                        style={{ backgroundColor: isActive ? palette.color : '#475569' }} 
                      />
                      <span className="font-medium text-[11px] truncate">{layer.display_name}</span>
                    </div>

                    <div className="flex items-center space-x-1.5">
                      {isLoading ? (
                        <RefreshCw className="w-3 h-3 text-cyan-400 animate-spin" />
                      ) : (
                        <span className="text-[10px] font-mono text-slate-400">
                          {layer.feature_count}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          {showVessels && (
            <div className="border-t border-slate-800 pt-2 text-[10px] font-mono">
              <span className={aisConnected ? 'text-emerald-400' : 'text-amber-400'}>
                {aisConnected ? `AIS live: ${vessels.length} vessels` : 'AIS feed unavailable'}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Selected Feature Inspector Drawer */}
      {selectedFeature && (
        <div className="absolute bottom-4 left-4 z-[1000] bg-[#091120]/95 backdrop-blur-md border border-cyan-500/40 rounded-xl p-3.5 shadow-2xl max-w-sm text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
            <div className="flex items-center space-x-1.5 text-cyan-400 font-bold">
              <ShieldCheck className="w-4 h-4" />
              <span>Spatial Feature Inspector</span>
            </div>
            <button 
              onClick={() => setSelectedFeature(null)} 
              className="text-slate-400 hover:text-white text-xs px-1 cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="space-y-1 font-mono text-[11px] text-slate-300 max-h-40 overflow-y-auto scrollbar-thin">
            {Object.entries(selectedFeature).slice(0, 6).map(([k, v]) => (
              <div key={k} className="flex justify-between py-0.5 border-b border-slate-800/40">
                <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}:</span>
                <span className="text-white font-semibold truncate ml-2 max-w-[160px]">{String(v)}</span>
              </div>
            ))}
          </div>

          <button
            onClick={() => {
              setSelectedItemForWhy(selectedFeature.name || selectedFeature.geoname || 'Spatial Maritime Entity');
              setWhyModalOpen(true);
            }}
            className="w-full mt-2 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-lg text-[10px] font-bold transition-colors flex items-center justify-center space-x-1.5 cursor-pointer"
          >
            <Info className="w-3.5 h-3.5" />
            <span>EXPLAIN SPATIAL REASONING</span>
          </button>
        </div>
      )}

      {/* Floating Active Marine Course HUD */}
      {course && course.origin && course.destination && (
        <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-[1000] bg-[#091120]/95 backdrop-blur-md border border-cyan-500/50 rounded-xl px-4 py-2.5 shadow-2xl max-w-xl w-[94%] sm:w-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-100">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 flex items-center justify-center shrink-0">
              <Compass className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Active Marine Course Track Plotted
              </div>
              <div className="font-bold text-white text-xs truncate max-w-[280px]">
                {course.origin.name} ➔ {course.destination.name}
              </div>
              <div className="text-[11px] text-slate-300 flex flex-wrap items-center gap-2 mt-0.5 font-mono">
                {course.distance && <span>Dist: <strong className="text-white">{course.distance}</strong></span>}
                {course.bearing && <span>• Brg: <strong className="text-cyan-300">{course.bearing.split(' ')[0]}</strong></span>}
                {course.fuelEstimate && <span>• Fuel: <strong className="text-amber-300">{course.fuelEstimate}</strong></span>}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end border-t sm:border-t-0 border-slate-800 pt-2 sm:pt-0">
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('marine:fit-course-bounds'));
              }}
              className="px-2.5 py-1.5 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 rounded-lg text-[11px] font-bold transition-colors cursor-pointer flex items-center gap-1"
              title="Fit Course in Map View"
            >
              <Navigation className="w-3 h-3" />
              <span>Fit View</span>
            </button>
            {onClearCourse && (
              <button
                onClick={onClearCourse}
                className="px-2.5 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 rounded-lg text-[11px] font-bold transition-colors cursor-pointer"
                title="Clear Course from Map"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}

      {/* Provenance Lineage Modal */}
      <ProvenanceModal
        isOpen={whyModalOpen}
        onClose={() => setWhyModalOpen(false)}
        recommendation={selectedItemForWhy || 'Maritime Boundary Spatial Analysis'}
      />
    </div>
  );
}
