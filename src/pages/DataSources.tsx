import React from 'react';
import { Database, Network, Radio, ShieldCheck, CheckCircle2, Clock, Activity, Cpu } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';

interface DataSource {
  name: string;
  agency: string;
  type: string;
  status: 'CONNECTED' | 'UNAVAILABLE' | 'SYNCING';
  latency: string;
  lastUpdate: string;
  records: string;
  frequency: string;
  payload: string;
}

const dataSourcesList: DataSource[] = [
  {
    name: 'MOSDAC / ISRO',
    agency: 'Space Applications Centre (SAC)',
    type: 'Satellite Oceanography (INSAT-3DR, Oceansat-3)',
    status: 'CONNECTED',
    latency: '182ms',
    lastUpdate: '12:42:18 UTC',
    records: '18,420 Rasters',
    frequency: 'Every 30 mins',
    payload: 'SST NetCDF4, Chlorophyll OCM-3, AOD'
  },
  {
    name: 'INCOIS ADVISORY CORE',
    agency: 'Ministry of Earth Sciences (MoES)',
    type: 'PFZ Multi-Spectral Bulletins & Ocean State',
    status: 'CONNECTED',
    latency: '145ms',
    lastUpdate: '12:41:50 UTC',
    records: '1,240 Bulletins',
    frequency: 'Daily 06:00 & 18:00',
    payload: 'PFZ Shapefiles, OSF Swell Alert Feed'
  },
  {
    name: 'IMD WEATHER STREAM',
    agency: 'India Meteorological Department',
    type: 'WRF Numerical Weather Predictions',
    status: 'CONNECTED',
    latency: '110ms',
    lastUpdate: '12:42:05 UTC',
    records: '9,860 Grid Points',
    frequency: 'Hourly 3km Grid',
    payload: '10m Wind U/V Vectors, Storm Tracks, CAPE'
  },
  {
    name: 'COPERNICUS MARINE (CMEMS)',
    agency: 'European Space Agency (ESA)',
    type: 'Global Hydrodynamic Physics Models',
    status: 'CONNECTED',
    latency: '320ms',
    lastUpdate: '12:38:00 UTC',
    records: '4,500 Profiles',
    frequency: 'Every 6 hours',
    payload: 'Global Salinity, Surface Current Vectors'
  },
  {
    name: 'AIS REAL-TIME TRACKING',
    agency: 'DG Shipping / Coastal AIS Network',
    type: 'Terrestrial & Satellite AIS Transponder Stream',
    status: 'CONNECTED',
    latency: '85ms',
    lastUpdate: '12:42:22 UTC',
    records: 'Live Vessels',
    frequency: 'Sub-second stream',
    payload: 'MMSI, SOG, COG, Lat/Lon, Vessel Class'
  },
  {
    name: 'GLOBAL FISHING WATCH',
    agency: 'GFW Research Pipeline',
    type: 'Historical Fishing Density & AIS Inference',
    status: 'UNAVAILABLE',
    latency: '240ms',
    lastUpdate: '12:00:00 UTC',
    records: '1.2M Vessel Hours',
    frequency: 'Daily Batch',
    payload: 'Apparent Fishing Effort (AFE) Rasters'
  }
];

export default function DataSources() {
  const { language } = useLanguage();

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5 space-y-6 font-sans select-none">
      
      {/* Top Header */}
      <div className="bg-white border border-[#D8E5EB] rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-bold text-[#176B87] uppercase tracking-wider flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-[#176B87]" />
              {language === 'ML' ? 'തത്സമയ വിവര സ്രോതസ്സുകൾ' : 'Telemetry & Satellite Feeds'}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-[#0B3954] flex items-center gap-2.5">
            <Database className="w-6 h-6 text-[#176B87]" />
            <span>{language === 'ML' ? 'മറൈൻ ഡാറ്റാ നെറ്റ്‌വർക്ക്' : 'Marine Data Ingestion Matrix'}</span>
          </h1>
          <p className="text-xs sm:text-sm text-[#5B7282] mt-1.5 max-w-2xl leading-relaxed">
            {language === 'ML'
              ? 'INCOIS, IMD, MOSDAC/ISRO മുതലായ കേന്ദ്രങ്ങളിൽ നിന്നുള്ള സാറ്റലൈറ്റ് വിവരങ്ങൾ മത്സ്യത്തൊഴിലാളികൾക്കായി തത്സമയം സംയോജിപ്പിക്കുന്നു.'
              : 'Live verified oceanographic feeds from INCOIS, IMD, MOSDAC/ISRO, and coastal radar networks feeding real-time safety & PFZ models.'}
          </p>
        </div>

        {/* Global Status Pill */}
        <div className="flex items-center space-x-2 shrink-0">
          <span className="text-xs bg-[#E8F7F0] text-[#16865B] px-3.5 py-2 rounded-xl border border-[#A6E2C6] font-bold flex items-center space-x-2 shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-[#16865B] animate-pulse" />
            <span>5 Active Streams • 1 Offline</span>
          </span>
        </div>
      </div>

      {/* Grid of Data Source Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {dataSourcesList.map((source, idx) => {
          const isConnected = source.status === 'CONNECTED';
          return (
            <div 
              key={idx} 
              className="bg-white border border-[#D8E5EB] rounded-2xl p-5 shadow-xs flex flex-col justify-between hover:border-[#176B87]/50 hover:shadow-sm transition-all"
            >
              <div>
                {/* Card Header */}
                <div className="flex items-start justify-between border-b border-[#E2EDF2] pb-3 mb-3.5 gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-[#0B3954]">{source.name}</h3>
                    <span className="text-xs text-[#176B87] font-medium">{source.agency}</span>
                  </div>
                  <span className={cn(
                    "text-[11px] px-2.5 py-1 rounded-lg font-bold border shrink-0 flex items-center gap-1.5",
                    isConnected 
                      ? "bg-[#E8F7F0] text-[#16865B] border-[#A6E2C6]" 
                      : "bg-[#FDF0EE] text-[#C0392B] border-[#F5C6CB]"
                  )}>
                    <span className={cn("w-1.5 h-1.5 rounded-full", isConnected ? "bg-[#16865B]" : "bg-[#C0392B]")} />
                    <span>{isConnected ? 'Connected' : 'Unavailable'}</span>
                  </span>
                </div>

                {/* Stream Type Details */}
                <div className="space-y-2 text-xs mb-4">
                  <div className="p-2.5 bg-[#F8FCFD] rounded-xl border border-[#E2EDF2]">
                    <span className="text-[10px] text-[#5B7282] block font-bold uppercase tracking-wider mb-0.5">Data Stream Type</span>
                    <span className="text-xs text-[#173042] font-semibold">{source.type}</span>
                  </div>
                  <div className="p-2.5 bg-[#F8FCFD] rounded-xl border border-[#E2EDF2]">
                    <span className="text-[10px] text-[#5B7282] block font-bold uppercase tracking-wider mb-0.5">Normalized Payloads</span>
                    <span className="text-xs text-[#0B3954] truncate block font-mono font-medium">{source.payload}</span>
                  </div>
                </div>
              </div>

              {/* Metrics Footer */}
              <div className="grid grid-cols-3 gap-2 pt-3 border-t border-[#E2EDF2] text-center text-xs">
                <div className="p-2 bg-[#F4F9FB] rounded-xl border border-[#E2EDF2]">
                  <span className="text-[#5B7282] uppercase block text-[9px] font-bold">Latency</span>
                  <span className="font-bold text-[#176B87] font-mono text-xs">{source.latency}</span>
                </div>
                <div className="p-2 bg-[#F4F9FB] rounded-xl border border-[#E2EDF2]">
                  <span className="text-[#5B7282] uppercase block text-[9px] font-bold">Update</span>
                  <span className="font-bold text-[#16865B] font-mono text-xs">{source.lastUpdate.substring(0, 8)}</span>
                </div>
                <div className="p-2 bg-[#F4F9FB] rounded-xl border border-[#E2EDF2]">
                  <span className="text-[#5B7282] uppercase block text-[9px] font-bold">Records</span>
                  <span className="font-bold text-[#0B3954] truncate block font-mono text-xs">{source.records.split(' ')[0]}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Orchestration Pipeline Topology */}
      <div className="bg-white border border-[#D8E5EB] rounded-2xl p-5 sm:p-6 shadow-xs">
        <div className="flex items-center space-x-2.5 mb-4 border-b border-[#E2EDF2] pb-3">
          <Network className="w-5 h-5 text-[#176B87]" />
          <div>
            <h2 className="text-sm sm:text-base font-bold text-[#0B3954]">
              Data Normalization & Multi-Agent Architecture
            </h2>
            <span className="text-xs text-[#5B7282]">
              Standardized pipeline delivering coastal intelligence in sub-200ms
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-[#F8FCFD] border border-[#D8E5EB]">
            <span className="text-xs text-[#176B87] font-black uppercase tracking-wider block mb-1">
              Stage 1: Ingestion & Decoding
            </span>
            <p className="text-xs text-[#5B7282] leading-relaxed">
              Receives HDF5, NetCDF, GeoTIFF rasters from MOSDAC/INCOIS and raw NMEA AIS sentences over secure authenticated feeds.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[#F8FCFD] border border-[#D8E5EB]">
            <span className="text-xs text-[#176B87] font-black uppercase tracking-wider block mb-1">
              Stage 2: Spatial-Temporal Fusion
            </span>
            <p className="text-xs text-[#5B7282] leading-relaxed">
              Interpolates satellite passes onto a continuous 1km coastal mesh for instant multi-layer overlay and geofence boundary audits.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[#F8FCFD] border border-[#D8E5EB]">
            <span className="text-xs text-[#176B87] font-black uppercase tracking-wider block mb-1">
              Stage 3: Offline Fishermen Sync
            </span>
            <p className="text-xs text-[#5B7282] leading-relaxed">
              Caches critical safety bulletins and high-yield PFZ zones onto device local storage for uninterrupted offline sea navigation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
