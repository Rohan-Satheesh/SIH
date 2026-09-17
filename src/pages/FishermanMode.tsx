import React, { useState, useEffect } from 'react';
import MarineMap from '../components/map/MarineMap';
import { 
  getSelectedLocation, 
  setSelectedLocation,
  type SelectedLocation 
} from '@/services/liveMarineService';

export default function FishermanMode() {
  const initialLoc = getSelectedLocation();
  const [currentLocation, setCurrentLocation] = useState<SelectedLocation>(initialLoc);
  const [mapCenter, setMapCenter] = useState<[number, number]>([initialLoc.lat, initialLoc.lng]);
  const [mapZoom, setMapZoom] = useState(8);

  useEffect(() => {
    const loc = getSelectedLocation();
    setCurrentLocation(loc);
    setMapCenter([loc.lat, loc.lng]);

    // Listen for coordinate / sector change from TopBar or Map
    const handleSectorChange = (e: any) => {
      const { lat, lng, name } = e.detail || {};
      if (typeof lat === 'number' && typeof lng === 'number') {
        const newLoc: SelectedLocation = { 
          lat, 
          lng, 
          name: name || `${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E` 
        };
        setCurrentLocation(newLoc);
        setSelectedLocation(newLoc);
        setMapCenter([lat, lng]);
      }
    };

    window.addEventListener('marine:sector-change', handleSectorChange);
    return () => window.removeEventListener('marine:sector-change', handleSectorChange);
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-125px)] md:h-[calc(100vh-110px)] overflow-hidden">
      {/* Full Interactive Leaflet Marine Map with PostGIS Spatial Layers */}
      <div className="flex-1 relative rounded-2xl overflow-hidden border border-[#D2E6ED] bg-white shadow-xs">
        <MarineMap 
          center={mapCenter} 
          zoom={mapZoom} 
          showPFZ={true} 
          showSST={true} 
          showChlorophyll={true}
          initialPinLabel={currentLocation.name}
        />
      </div>
    </div>
  );
}
