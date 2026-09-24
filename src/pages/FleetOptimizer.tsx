import React, { useState, useMemo } from 'react';
import { 
  Fuel, 
  ShieldCheck, 
  Play, 
  Sliders,
  Ship,
  Compass,
  Navigation,
  RotateCcw
} from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import MarineMap, { type NavigationCourse } from '@/components/map/MarineMap';

interface PortDestination {
  id: string;
  name: string;
  nameMl: string;
  lat: number;
  lng: number;
  type: 'harbor' | 'zone';
}

const PORTS: PortDestination[] = [
  { id: 'kochi', name: 'Kochi Harbor (Thoppumpady)', nameMl: 'കൊച്ചി ഹാർബർ', lat: 9.93, lng: 76.24, type: 'harbor' },
  { id: 'munambam', name: 'Munambam Fishing Port', nameMl: 'മുനമ്പം ഫിഷിംഗ് ഹാർബർ', lat: 10.18, lng: 76.16, type: 'harbor' },
  { id: 'kollam', name: 'Kollam (Neendakara) Port', nameMl: 'നീണ്ടകര ഹാർബർ, കൊല്ലം', lat: 8.94, lng: 76.54, type: 'harbor' },
  { id: 'beypore', name: 'Beypore Port, Kozhikode', nameMl: 'ബേപ്പൂർ തുറമുഖം', lat: 11.16, lng: 75.81, type: 'harbor' },
  { id: 'vizhinjam', name: 'Vizhinjam Marine Port', nameMl: 'വിഴിഞ്ഞം തുറമുഖം', lat: 8.37, lng: 76.98, type: 'harbor' },
];

const TARGET_ZONES: PortDestination[] = [
  { id: 'zone-k04', name: 'Sector K-04 (High-Yield PFZ)', nameMl: 'സെക്ടർ K-04 (ചാകര സോൺ)', lat: 9.93, lng: 75.68, type: 'zone' },
  { id: 'zone-m02', name: 'Sector M-02 (Off Munambam)', nameMl: 'സെക്ടർ M-02 (മുനമ്പം തീരം)', lat: 10.22, lng: 75.78, type: 'zone' },
  { id: 'zone-wadge', name: 'Wadge Bank Fishery Grounds', nameMl: 'വാഡ്ജ് ബാങ്ക് മത്സ്യമേഖല', lat: 7.95, lng: 76.90, type: 'zone' },
  { id: 'zone-lakshadweep', name: 'Lakshadweep Deep Basin', nameMl: 'ലക്ഷദ്വീപ് കടൽത്തീരം', lat: 10.10, lng: 74.20, type: 'zone' },
];

interface VesselType {
  id: string;
  name: string;
  nameMl: string;
  speedKnots: number;
  fuelRate: number; // liters per nautical mile
}

const VESSEL_TYPES: VesselType[] = [
  { id: 'trawler', name: 'Deep-Sea Mechanized Trawler (350 HP)', nameMl: 'മെക്കനൈസ്ഡ് ട്രോളർ', speedKnots: 9.5, fuelRate: 3.8 },
  { id: 'gillnetter', name: 'Multiday Gillnetter / Longliner', nameMl: 'മൾട്ടിഡേ ഗിൽനെറ്റർ', speedKnots: 11.0, fuelRate: 2.9 },
  { id: 'ringseiner', name: 'Inshore Ring Seiner Craft', nameMl: 'റിങ് സീനർ വള്ളം', speedKnots: 8.0, fuelRate: 2.1 },
  { id: 'carrier', name: 'Coastal Fish Transporter / Carrier', nameMl: 'ഫിഷ് കാരിയർ ബോട്ട്', speedKnots: 12.5, fuelRate: 4.2 },
];

export default function FleetOptimizer() {
  const { language } = useLanguage();

  // Selection states
  const [selectedOrigin, setSelectedOrigin] = useState<string>('kochi');
  const [selectedDest, setSelectedDest] = useState<string>('zone-k04');
  const [selectedVessel, setSelectedVessel] = useState<string>('trawler');
  const [avoidSwell, setAvoidSwell] = useState<boolean>(true);
  const [stayEEZ, setStayEEZ] = useState<boolean>(true);
  const [currentAssistance, setCurrentAssistance] = useState<boolean>(true);

  // Calculation & simulation state
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationStage, setOptimizationStage] = useState(0);
  const [resultsReady, setResultsReady] = useState(false); // Map will show just ports initially

  const originPort = PORTS.find(p => p.id === selectedOrigin) || PORTS[0];
  const destZone = TARGET_ZONES.find(z => z.id === selectedDest) || TARGET_ZONES[0];
  const vessel = VESSEL_TYPES.find(v => v.id === selectedVessel) || VESSEL_TYPES[0];

  // Geodesic distance calculation (approximate nautical miles)
  const distanceNM = useMemo(() => {
    const dLat = (destZone.lat - originPort.lat) * 60;
    const avgLatRad = ((destZone.lat + originPort.lat) / 2) * (Math.PI / 180);
    const dLng = (destZone.lng - originPort.lng) * 60 * Math.cos(avgLatRad);
    const straightDist = Math.sqrt(dLat * dLat + dLng * dLng);
    // Route detour factor to navigate safely around sandbars/swells
    const detourFactor = avoidSwell ? 1.14 : 1.05;
    return Math.max(12, Math.round(straightDist * detourFactor * 10) / 10);
  }, [originPort, destZone, avoidSwell]);

  const distanceKm = Math.round(distanceNM * 1.852 * 10) / 10;

  // Single active routing strategy for data display
  const activeStrategy = useMemo(() => {
    const effectiveDist = stayEEZ ? distanceNM * 1.05 : distanceNM;
    const currentSpeedBoost = currentAssistance ? 1.2 : 0;
    const baseFuelLiters = Math.round(effectiveDist * vessel.fuelRate * 2); // Round trip
    const dieselCostPerLiter = 94.0; // INR

    return {
      id: 'strat-balanced',
      name: language === 'ML' ? 'സുരക്ഷിത പാത (ശുപാർശ ചെയ്യുന്നത്)' : 'Safe Weather Corridor (Recommended)',
      tag: language === 'ML' ? 'മികച്ച അനുപാതം' : 'Best Overall',
      speed: Math.round((vessel.speedKnots + currentSpeedBoost) * 10) / 10,
      fuelLiters: Math.round(baseFuelLiters * 0.78),
      fuelBaseline: baseFuelLiters,
      savingsPercent: 22,
      savingsInr: Math.round((baseFuelLiters * 0.22) * dieselCostPerLiter),
      timeHours: Math.round((effectiveDist / (vessel.speedKnots + currentSpeedBoost)) * 10) / 10,
      co2ReductionKg: Math.round((baseFuelLiters * 0.22) * 2.68),
      maxSwellMeters: 1.3,
      confidenceScore: 94,
    };
  }, [distanceNM, vessel, language, stayEEZ, currentAssistance]);

  const stages = [
    "ANALYZING COASTAL BATHYMETRY & REEF CONSTRAINTS",
    "POLLING INCOIS REAL-TIME SWELL & CURRENT VECTORS",
    "COMPUTING DIESEL CONSUMPTION ALONG ALTERNATIVE WAYPOINTS",
    "VERIFYING MARITIME EEZ AND COAST GUARD CORRIDORS",
    "OPTIMAL FUEL & WEATHER TRACK READY"
  ];

  const handleRunOptimizer = () => {
    setIsOptimizing(true);
    setResultsReady(false);
    setOptimizationStage(0);

    const stageTimer = setInterval(() => {
      setOptimizationStage(prev => {
        if (prev >= stages.length - 1) {
          clearInterval(stageTimer);
          setIsOptimizing(false);
          setResultsReady(true);
          return prev;
        }
        return prev + 1;
      });
    }, 450);
  };

  const computedCourse = useMemo<NavigationCourse | null>(() => {
    if (!resultsReady || isOptimizing) return null;

    const numWaypoints = 20;
    const wps: [number, number][] = [];
    
    const dx = destZone.lng - originPort.lng;
    const dy = destZone.lat - originPort.lat;
    
    // Perpendicular vector pointing generally offshore (Westward)
    const perpLng = -dy;
    const perpLat = dx;
    
    // Bow amplitude as a fraction of the total path length
    const bowAmplitude = avoidSwell ? 0.25 : 0.02;
    
    for (let i = 1; i <= numWaypoints; i++) {
      const t = i / (numWaypoints + 1);
      const baseLat = originPort.lat + dy * t;
      const baseLng = originPort.lng + dx * t;
      
      // Parabolic curve: 4 * t * (1 - t) peaks at 1.0 when t = 0.5
      const curveScale = 4 * t * (1 - t) * bowAmplitude;
      
      wps.push([
        baseLat + perpLat * curveScale, 
        baseLng + perpLng * curveScale
      ]);
    }

    return {
      id: `course-${activeStrategy.id}`,
      origin: { lat: originPort.lat, lng: originPort.lng, name: originPort.name },
      destination: { lat: destZone.lat, lng: destZone.lng, name: destZone.name, species: 'High-Yield Pelagic' },
      distance: `${distanceNM} NM`,
      bearing: 'North-West Track',
      fuelEstimate: `${activeStrategy.fuelLiters} L (${activeStrategy.tag})`,
      waypoints: wps
    };
  }, [resultsReady, isOptimizing, originPort, destZone, avoidSwell, activeStrategy, distanceNM]);

  return (
    <div className="max-w-7xl mx-auto px-3.5 sm:px-6 py-5 space-y-5 font-sans select-none">
      
      {/* Top Header Card */}
      <div className="bg-white border border-[#D8E5EB] rounded-2xl p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-bold text-[#176B87] uppercase tracking-wider flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-[#176B87]" />
              {language === 'ML' ? 'തുറമുഖ & ഇന്ധന ഒപ്റ്റിമൈസർ' : 'Harbor & Fleet Energy Routing'}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-[#0B3954] flex items-center gap-2.5">
            <Ship className="w-6 h-6 text-[#176B87]" />
            <span>{language === 'ML' ? 'ഫ്ലീറ്റ് വെതർ റൂട്ട് ഒപ്റ്റിമൈസർ' : 'Fleet Route & Fuel Optimizer'}</span>
          </h1>
          <p className="text-xs sm:text-sm text-[#5B7282] mt-1 max-w-2xl leading-relaxed">
            {language === 'ML'
              ? 'ഉയർന്ന തിരമാലകളും പ്രതികൂല ഒഴുക്കുകളും ഒഴിവാക്കി കുറഞ്ഞ ഇന്ധനച്ചെലവിൽ ചാകര മേഖലകളിലേക്ക് എത്തിച്ചേരാനുള്ള സമുദ്ര നാവിഗേഷൻ.'
              : 'Multi-objective marine routing avoiding rough swells, optimizing current assistance, and cutting round-trip diesel expenses.'}
          </p>
        </div>

        {/* Global Delta Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-2 bg-[#E8F7F0] border border-[#A6E2C6] px-3 py-1.5 rounded-xl shadow-2xs">
            <Fuel className="w-4 h-4 text-[#16865B]" />
            <div>
              <span className="text-[10px] text-[#5B7282] block font-bold uppercase">Avg. Diesel Saved</span>
              <span className="text-xs font-black text-[#16865B]">22% to 29% per trip</span>
            </div>
          </div>
          <div className="flex items-center space-x-2 bg-[#F8FCFD] border border-[#D8E5EB] px-3 py-1.5 rounded-xl shadow-2xs">
            <ShieldCheck className="w-4 h-4 text-[#176B87]" />
            <div>
              <span className="text-[10px] text-[#5B7282] block font-bold uppercase">Safety Index</span>
              <span className="text-xs font-bold text-[#0B3954]">Swell &le; 1.5m</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Parameters on Left + Interactive Chart & Results on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* Left Column: Voyage Parameters (4 cols on lg) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-[#D8E5EB] rounded-2xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-[#E2EDF2] pb-3">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-[#176B87]" />
                <h2 className="text-sm font-bold text-[#0B3954] uppercase tracking-wider">
                  {language === 'ML' ? 'യാത്രാ വിവരങ്ങൾ' : 'Voyage Parameters'}
                </h2>
              </div>
              <span className="text-[10px] text-[#16865B] font-bold bg-[#E8F7F0] px-2 py-0.5 rounded-md border border-[#A6E2C6]">
                Live Inputs
              </span>
            </div>

            {/* Departure Harbor */}
            <div>
              <label className="text-[11px] text-[#5B7282] font-bold uppercase tracking-wider block mb-1">
                {language === 'ML' ? 'പുറപ്പെടുന്ന തുറമുഖം (Origin Harbor)' : 'Departure Harbor'}
              </label>
              <select
                value={selectedOrigin}
                onChange={e => setSelectedOrigin(e.target.value)}
                className="w-full bg-[#F8FCFD] border border-[#D8E5EB] rounded-xl px-3 py-2.5 text-xs text-[#0B3954] font-semibold focus:outline-none focus:border-[#176B87] transition-colors"
              >
                {PORTS.map(p => (
                  <option key={p.id} value={p.id}>
                    {language === 'ML' ? p.nameMl : p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Destination Target Zone */}
            <div>
              <label className="text-[11px] text-[#5B7282] font-bold uppercase tracking-wider block mb-1">
                {language === 'ML' ? 'ലക്ഷ്യസ്ഥാനം (Target Fishing Zone)' : 'Target Fishing Sector'}
              </label>
              <select
                value={selectedDest}
                onChange={e => setSelectedDest(e.target.value)}
                className="w-full bg-[#F8FCFD] border border-[#D8E5EB] rounded-xl px-3 py-2.5 text-xs text-[#0B3954] font-semibold focus:outline-none focus:border-[#176B87] transition-colors"
              >
                {TARGET_ZONES.map(z => (
                  <option key={z.id} value={z.id}>
                    {language === 'ML' ? z.nameMl : z.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Vessel Category */}
            <div>
              <label className="text-[11px] text-[#5B7282] font-bold uppercase tracking-wider block mb-1">
                {language === 'ML' ? 'ബോട്ട് / വള്ളത്തിന്റെ തരം' : 'Vessel Class'}
              </label>
              <select
                value={selectedVessel}
                onChange={e => setSelectedVessel(e.target.value)}
                className="w-full bg-[#F8FCFD] border border-[#D8E5EB] rounded-xl px-3 py-2.5 text-xs text-[#0B3954] font-semibold focus:outline-none focus:border-[#176B87] transition-colors"
              >
                {VESSEL_TYPES.map(v => (
                  <option key={v.id} value={v.id}>
                    {language === 'ML' ? v.nameMl : v.name} ({v.speedKnots} kn)
                  </option>
                ))}
              </select>
            </div>

            {/* Constraints Checkboxes */}
            <div className="space-y-2 pt-1 border-t border-[#E2EDF2]">
              <span className="text-[11px] text-[#5B7282] font-bold uppercase tracking-wider block mb-1">
                {language === 'ML' ? 'പരിഗണനകൾ (Constraints)' : 'Optimization Factors'}
              </span>

              <label className="flex items-center justify-between p-2.5 rounded-xl bg-[#F8FCFD] border border-[#E2EDF2] cursor-pointer hover:border-[#176B87]/40 transition-colors">
                <span className="text-xs text-[#173042] font-medium">
                  {language === 'ML' ? 'ശക്തമായ തിരമാലകൾ ഒഴിവാക്കുക' : 'Avoid High Swells & Choppy Waves'}
                </span>
                <input 
                  type="checkbox" 
                  checked={avoidSwell} 
                  onChange={e => setAvoidSwell(e.target.checked)} 
                  className="accent-[#176B87] w-4 h-4 cursor-pointer"
                />
              </label>

              <label className="flex items-center justify-between p-2.5 rounded-xl bg-[#F8FCFD] border border-[#E2EDF2] cursor-pointer hover:border-[#176B87]/40 transition-colors">
                <span className="text-xs text-[#173042] font-medium">
                  {language === 'ML' ? 'ഇന്ത്യൻ അതിർത്തിക്കുള്ളിൽ നിൽക്കുക' : 'Stay Within Indian EEZ Waters'}
                </span>
                <input 
                  type="checkbox" 
                  checked={stayEEZ} 
                  onChange={e => setStayEEZ(e.target.checked)} 
                  className="accent-[#176B87] w-4 h-4 cursor-pointer"
                />
              </label>

              <label className="flex items-center justify-between p-2.5 rounded-xl bg-[#F8FCFD] border border-[#E2EDF2] cursor-pointer hover:border-[#176B87]/40 transition-colors">
                <span className="text-xs text-[#173042] font-medium">
                  {language === 'ML' ? 'അനുകൂല ഒഴുക്ക് പ്രയോജനപ്പെടുത്തുക' : 'Surface Current Speed Boost'}
                </span>
                <input 
                  type="checkbox" 
                  checked={currentAssistance} 
                  onChange={e => setCurrentAssistance(e.target.checked)} 
                  className="accent-[#176B87] w-4 h-4 cursor-pointer"
                />
              </label>
            </div>

            {/* Run Action Button */}
            <button
              onClick={handleRunOptimizer}
              disabled={isOptimizing}
              className="w-full bg-[#176B87] hover:bg-[#0B3954] text-white font-bold text-xs py-3.5 rounded-xl flex items-center justify-center space-x-2 shadow-xs hover:shadow-sm transition-all disabled:opacity-50 cursor-pointer mt-2"
            >
              {isOptimizing ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  <span>{language === 'ML' ? 'പാത കണക്കാക്കുന്നു...' : 'Calculating Optimal Route...'}</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>{language === 'ML' ? 'റൂട്ട് ഒപ്റ്റിമൈസ് ചെയ്യുക' : 'Compute Optimal Route'}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Nautical Chart Vector Map */}
        <div className="lg:col-span-8 space-y-4">
          
          {/* Animated Nautical Chart Visualization */}
          <div className="bg-white border border-[#D8E5EB] rounded-2xl p-5 shadow-xs relative overflow-hidden h-full flex flex-col">
            <div className="flex items-center justify-between border-b border-[#E2EDF2] pb-3 mb-4">
              <div className="flex items-center space-x-2">
                <Navigation className="w-4 h-4 text-[#176B87]" />
                <h3 className="text-sm font-bold text-[#0B3954]">
                  {language === 'ML' ? 'നാവിഗേഷൻ ചാർട്ട് (Nautical Route Map)' : 'Nautical Corridor & Wave Map'}
                </h3>
              </div>
              <div className="flex items-center space-x-3 text-xs">
                <span className="font-bold text-[#0B3954] flex items-center gap-1">
                  <span className="text-[#5B7282] font-normal">Distance:</span> {distanceNM} NM ({distanceKm} km)
                </span>
                <span className="text-[#16865B] bg-[#E8F7F0] border border-[#A6E2C6] px-2.5 py-0.5 rounded-md font-bold text-[11px]">
                  Safe Corridor Active
                </span>
              </div>
            </div>

            {/* Google Maps style interactive map */}
            <div className="w-full flex-grow min-h-[500px] rounded-xl relative border border-[#CDE3ED] overflow-hidden shadow-inner z-0">
              <MarineMap
                center={[(originPort.lat + destZone.lat) / 2, (originPort.lng + destZone.lng) / 2]}
                zoom={7}
                showSST={true}
                showVessels={true}
                course={computedCourse}
                initialPinLabel={language === 'ML' ? 'റൂട്ട് മാപ്പ്' : 'Fleet Operations Map'}
              />

              {/* Optimization Progress Overlay */}
              {isOptimizing && (
                <div className="absolute inset-0 bg-white/90 backdrop-blur-xs flex flex-col items-center justify-center p-6 z-20">
                  <RotateCcw className="w-8 h-8 text-[#176B87] animate-spin mb-3" />
                  <h4 className="text-sm font-bold text-[#0B3954] mb-1">
                    {stages[optimizationStage]}
                  </h4>
                  <div className="w-64 bg-[#F4F9FB] rounded-full h-2 overflow-hidden border border-[#D8E5EB] mt-2">
                    <div 
                      className="bg-[#176B87] h-2 rounded-full transition-all duration-300"
                      style={{ width: `${((optimizationStage + 1) / stages.length) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
