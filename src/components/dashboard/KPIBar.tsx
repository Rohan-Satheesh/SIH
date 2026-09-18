import React, { useState, useEffect, useRef } from 'react';
import { 
  Thermometer, 
  Waves, 
  Wind, 
  Ship, 
  ShieldAlert, 
  Cpu, 
  MapPin, 
  Crosshair, 
  ChevronDown, 
  Loader2, 
  Search, 
  Check,
  Navigation
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiUrl } from '@/services/api';
import { 
  fetchLiveMarineData, 
  getCachedMarineData, 
  COASTAL_SECTORS, 
  getNearestCoastalSector, 
  type LiveMarineData, 
  type CoastalSector 
} from '@/services/liveMarineService';

interface AISStatus {
  connected: boolean;
  count?: number;
  message?: string;
}

export default function KPIBar() {
  const [data, setData] = useState<LiveMarineData>(getCachedMarineData());
  const [ais, setAis] = useState<AISStatus>({ connected: false });
  const [selectedSector, setSelectedSector] = useState<CoastalSector>(COASTAL_SECTORS[0]);
  const [activeLocationLabel, setActiveLocationLabel] = useState<string>(COASTAL_SECTORS[0].name);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isDetectingGps, setIsDetectingGps] = useState(false);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch telemetry for specific coordinates
  const loadTelemetry = async (lat: number, lng: number, label: string, notifyMap: boolean = true) => {
    setIsRefreshing(true);
    try {
      const result = await fetchLiveMarineData(lat, lng, label, true);
      setData(result);
      setActiveLocationLabel(label);

      if (notifyMap) {
        window.dispatchEvent(new CustomEvent('marine:sector-change', {
          detail: { lat, lng, name: label }
        }));
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    // Initial fetch for default sector
    loadTelemetry(selectedSector.lat, selectedSector.lng, selectedSector.name, false);

    const fetchAis = () => fetch(apiUrl('/api/ais/vessels'))
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then(setAis)
      .catch(() => setAis({ connected: false }));
    fetchAis();

    // Listen for coordinate clicks on the map
    const handleMapSelect = (e: any) => {
      if (e.detail?.fromMapClick) {
        const { lat, lng, name } = e.detail;
        loadTelemetry(lat, lng, name, false);
      }
    };
    window.addEventListener('marine:sector-change', handleMapSelect);

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      loadTelemetry(data.latitude, data.longitude, activeLocationLabel, false);
      fetchAis();
    }, 60000);

    return () => {
      clearInterval(interval);
      window.removeEventListener('marine:sector-change', handleMapSelect);
    };
  }, []);

  // Handle Sector Selection
  const handleSelectSector = (sector: CoastalSector) => {
    setSelectedSector(sector);
    setGpsError(null);
    setDropdownOpen(false);
    loadTelemetry(sector.lat, sector.lng, sector.name);
  };

  // Handle User GPS Geolocation Detection
  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser');
      return;
    }

    setIsDetectingGps(true);
    setGpsError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const { sector, distanceKm } = getNearestCoastalSector(latitude, longitude);
        
        let label = `GPS Fix (${latitude.toFixed(2)}°N, ${longitude.toFixed(2)}°E)`;
        if (distanceKm > 20) {
          label = `GPS (${distanceKm}km off ${sector.name.split(' ')[0]})`;
        }

        loadTelemetry(latitude, longitude, label);
        setIsDetectingGps(false);
        setDropdownOpen(false);
      },
      (err) => {
        setIsDetectingGps(false);
        if (err.code === err.PERMISSION_DENIED) {
          setGpsError('Location permission denied. Please allow GPS access in your browser.');
        } else {
          setGpsError('Unable to acquire satellite GPS fix.');
        }
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const filteredSectors = COASTAL_SECTORS.filter(s => 
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.region.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const kpis = [
    { 
      label: 'SST Thermal', 
      value: data.sst === null ? '—' : `${data.sst}°C`, 
      detail: data.sstAnomaly === null ? 'Unavailable' : `${data.sstAnomaly >= 0 ? '+' : ''}${data.sstAnomaly}° anomaly`, 
      icon: Thermometer, 
      color: 'text-rose-400' 
    },
    { 
      label: 'Wave Height', 
      value: data.waveHeight === null ? '—' : `${data.waveHeight}m`, 
      detail: data.wavePeriod === null ? 'Unavailable' : `${data.wavePeriod}s period`, 
      icon: Waves, 
      color: 'text-blue-400' 
    },
    { 
      label: 'Surface Wind', 
      value: data.windSpeed === null ? '—' : `${data.windSpeed} km/h`, 
      detail: data.windDirection === null ? 'Unavailable' : `${data.windDirection}° heading`, 
      icon: Wind, 
      color: 'text-emerald-400' 
    },
    { 
      label: 'AIS Active', 
      value: ais.connected ? String(ais.count ?? 0) : '—', 
      detail: ais.connected ? 'live vessels' : 'AIS feed not connected', 
      icon: Ship, 
      color: 'text-cyan-400' 
    },
    { 
      label: 'Maritime Risk', 
      value: data.isLive ? `${data.riskLevel} RISK` : '—', 
      detail: data.riskScore === null ? 'Awaiting telemetry' : `Score ${data.riskScore}/100`, 
      icon: ShieldAlert, 
      color: data.riskLevel === 'LOW' ? 'text-emerald-400' : data.riskLevel === 'MEDIUM' ? 'text-amber-400' : 'text-rose-400' 
    },
    { 
      label: 'AI Agents', 
      value: '—', 
      detail: 'Agent telemetry not connected', 
      icon: Cpu, 
      color: 'text-cyan-300' 
    },
  ];

  return (
    <div className="relative z-40 h-12 w-full border-b border-slate-800/80 bg-[#070D18]/95 backdrop-blur-md flex items-center px-3.5 flex-shrink-0 select-none">
      
      {/* Location / Sector Dropdown Selector (Unclipped) */}
      <div className="relative flex-shrink-0" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setDropdownOpen(prev => !prev)}
          className={cn(
            "flex items-center space-x-2 px-2.5 py-1 rounded-md border transition-all text-xs group cursor-pointer shadow-sm",
            dropdownOpen
              ? "bg-cyan-950/60 border-cyan-400/80 text-cyan-200 ring-1 ring-cyan-400/50"
              : "bg-slate-900/90 border-slate-700/80 hover:border-cyan-500/60 hover:bg-slate-800/60 text-slate-200"
          )}
          title="Change monitored ocean sector or use GPS location"
        >
          <div className="w-5 h-5 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center flex-shrink-0">
            {isRefreshing ? (
              <Loader2 className="w-3 h-3 text-cyan-400 animate-spin" />
            ) : (
              <MapPin className="w-3 h-3 text-cyan-400 group-hover:scale-110 transition-transform" />
            )}
          </div>
          
          <div className="flex flex-col text-left min-w-0 pr-1">
            <span className="text-[9px] uppercase tracking-wider text-cyan-400 font-bold leading-tight flex items-center gap-1">
              Sector / GPS
              {isRefreshing && <span className="w-1 h-1 rounded-full bg-cyan-400 animate-ping" />}
            </span>
            <span className="text-xs font-bold text-white truncate max-w-[135px] sm:max-w-[170px] leading-tight font-sans">
              {activeLocationLabel}
            </span>
          </div>

          <ChevronDown className={cn("w-3.5 h-3.5 text-slate-400 transition-transform duration-200 flex-shrink-0", dropdownOpen && "rotate-180 text-cyan-400")} />
        </button>

        {/* Floating Sector Picker Modal */}
        {dropdownOpen && (
          <div 
            onClick={(e) => e.stopPropagation()}
            className="absolute left-0 top-full mt-2 w-80 sm:w-96 bg-[#07111F]/98 backdrop-blur-2xl border border-slate-700/90 rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.85)] z-50 p-3 text-slate-200 animate-in fade-in zoom-in-95 duration-150"
          >
            {/* Auto-detect GPS button */}
            <button
              type="button"
              onClick={handleDetectLocation}
              disabled={isDetectingGps}
              className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/40 text-cyan-300 text-xs font-semibold transition-colors cursor-pointer group"
            >
              {isDetectingGps ? (
                <Loader2 className="w-4 h-4 animate-spin text-cyan-400 flex-shrink-0" />
              ) : (
                <Crosshair className="w-4 h-4 text-cyan-400 group-hover:rotate-45 transition-transform flex-shrink-0" />
              )}
              <div className="flex flex-col text-left min-w-0">
                <span className="font-semibold text-white">
                  {isDetectingGps ? 'Acquiring GPS fix...' : 'Use My GPS Location'}
                </span>
                <span className="text-[10px] text-cyan-400/80 truncate">
                  Auto-detect browser coordinates & fetch live ocean telemetry
                </span>
              </div>
            </button>

            {gpsError && (
              <div className="mt-2 text-[11px] text-rose-400 bg-rose-500/10 border border-rose-500/30 rounded-md px-2.5 py-1.5 leading-snug">
                {gpsError}
              </div>
            )}

            {/* Divider */}
            <div className="flex items-center my-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
              <span className="flex-1 border-b border-slate-800" />
              <span className="px-2">or select coastal sector</span>
              <span className="flex-1 border-b border-slate-800" />
            </div>

            {/* Search Filter */}
            <div className="relative mb-2">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search sector or port (e.g. Mumbai, Goa)..."
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/60"
              />
            </div>

            {/* Sectors List */}
            <div className="max-h-60 overflow-y-auto space-y-1 pr-1 scrollbar-thin">
              {filteredSectors.map((sector) => {
                const isSelected = activeLocationLabel === sector.name;
                return (
                  <button
                    key={sector.id}
                    type="button"
                    onClick={() => handleSelectSector(sector)}
                    className={cn(
                      "w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition-colors cursor-pointer text-xs",
                      isSelected
                        ? "bg-cyan-500/20 border border-cyan-500/40 text-cyan-200 font-semibold"
                        : "hover:bg-slate-800/60 text-slate-300 hover:text-white border border-transparent"
                    )}
                  >
                    <div className="flex flex-col min-w-0 pr-2">
                      <span className="truncate font-medium">{sector.name}</span>
                      <span className="text-[10px] text-slate-400 truncate">{sector.region}</span>
                    </div>

                    <div className="flex items-center space-x-1.5 flex-shrink-0">
                      <span className="text-[10px] font-mono text-slate-500">
                        {sector.lat.toFixed(1)}°N, {sector.lng.toFixed(1)}°E
                      </span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-cyan-400" />}
                    </div>
                  </button>
                );
              })}

              {filteredSectors.length === 0 && (
                <div className="text-center py-4 text-xs text-slate-500">
                  No coastal sectors match "{searchQuery}"
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="h-6 w-px bg-slate-800 flex-shrink-0 mx-2" />

      {/* KPI Cards (Scrollable on small screens) */}
      <div className="flex-1 flex items-center overflow-x-auto scrollbar-none gap-2 min-w-0">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div 
              key={idx} 
              className="flex-1 min-w-[140px] flex items-center space-x-2 px-2.5 py-1 rounded-md hover:bg-slate-800/40 transition-colors"
            >
              <div className="w-6 h-6 rounded bg-slate-900 border border-slate-800 flex items-center justify-center flex-shrink-0">
                <Icon className={cn("w-3.5 h-3.5", kpi.color)} />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[10px] text-slate-400 font-medium truncate leading-tight">
                  {kpi.label}
                </span>
                <div className="flex items-baseline space-x-1.5 leading-tight">
                  <span className="text-xs font-bold text-white font-mono">
                    {kpi.value}
                  </span>
                  <span className="text-[10px] text-slate-400 truncate">
                    {kpi.detail}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

