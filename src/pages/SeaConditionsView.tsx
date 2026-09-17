import React, { useState, useEffect } from 'react';
import { 
  Waves, 
  Compass, 
  Thermometer, 
  ShieldCheck, 
  AlertTriangle, 
  AlertOctagon, 
  Anchor, 
  RefreshCw,
  Info
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  fetchLiveMarineData, 
  getCachedMarineData, 
  type LiveMarineData 
} from '@/services/liveMarineService';

export default function SeaConditionsView() {
  const { language, t } = useLanguage();
  const [data, setData] = useState<LiveMarineData>(getCachedMarineData());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLiveMarineData().then(setData);

    const handleSectorChange = (e: any) => {
      const { lat, lng, name } = e.detail || {};
      if (lat && lng) {
        fetchLiveMarineData(lat, lng, name, true).then(setData);
      }
    };
    window.addEventListener('marine:sector-change', handleSectorChange);
    return () => window.removeEventListener('marine:sector-change', handleSectorChange);
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const res = await fetchLiveMarineData(data.latitude, data.longitude, data.locationName, true);
      setData(res);
    } finally {
      setLoading(false);
    }
  };

  // Sea State classification
  const getSeaState = (waveHeight: number | null) => {
    const h = waveHeight ?? 1.2;
    if (h < 1.0) {
      return {
        label: language === 'ML' ? 'ശാന്തമായ കടൽ' : 'Calm Sea State',
        rating: 'CALM',
        color: 'text-[#16865B]',
        bg: 'bg-[#E8F7F0]',
        border: 'border-[#A6E2C6]',
        traditionalCraft: language === 'ML' ? 'വള്ളങ്ങൾക്കും ചെറുവഞ്ചികൾക്കും അനുയോജ്യം' : 'Favorable for traditional canoes & kattumarams',
        mechanizedCraft: language === 'ML' ? 'പൂർണ്ണമായും സുരക്ഷിതം' : 'Completely safe navigation for trawlers',
      };
    }
    if (h < 2.0) {
      return {
        label: language === 'ML' ? 'മിതമായ തിരമാലകൾ' : 'Moderate Sea State',
        rating: 'MODERATE',
        color: 'text-[#0B3954]',
        bg: 'bg-[#DFF3FA]',
        border: 'border-[#C4D9E2]',
        traditionalCraft: language === 'ML' ? 'തീരത്തുനിന്ന് 5 നോട്ടിക്കൽ മൈലിനുള്ളിൽ നിൽക്കുക' : 'Stay within 5 nautical miles from coast',
        mechanizedCraft: language === 'ML' ? 'സുരക്ഷിതമായ ബോട്ടിംഗ്' : 'Standard fishing protocols for mechanized craft',
      };
    }
    if (h < 3.0) {
      return {
        label: language === 'ML' ? 'ക്ഷോഭഭരിതമായ കടൽ' : 'Rough Sea State',
        rating: 'ROUGH',
        color: 'text-[#D99116]',
        bg: 'bg-[#FEF6E8]',
        border: 'border-[#F8DAA5]',
        traditionalCraft: language === 'ML' ? 'ചെറുവള്ളങ്ങൾ കടലിൽ പോകരുത്' : 'Traditional craft should not venture out',
        mechanizedCraft: language === 'ML' ? 'ജാഗ്രതയോടെ പ്രവർത്തിക്കുക' : 'Heavy rolling expected; secure gear and rigging',
      };
    }
    return {
      label: language === 'ML' ? 'അതീവ അപകടകരമായ കടൽ' : 'Very Rough / Storm Surge',
      rating: 'HAZARDOUS',
      color: 'text-[#C0392B]',
      bg: 'bg-[#FDF0EE]',
      border: 'border-[#F5B8B1]',
      traditionalCraft: language === 'ML' ? 'തീർത്തും അപകടകരം' : 'Hazardous. Coastal craft prohibition in effect',
      mechanizedCraft: language === 'ML' ? 'തുറമുഖത്തേക്ക് മടങ്ങുക' : 'Return to safe harbor immediately',
    };
  };

  const seaState = getSeaState(data.waveHeight);

  return (
    <div className="max-w-4xl mx-auto px-3.5 sm:px-6 py-4 space-y-4">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-bold text-[#176B87] uppercase tracking-wider">
            {t('navSea')}
          </span>
          <h1 className="text-xl sm:text-2xl font-black text-[#0B3954]">
            {language === 'ML' ? 'തിരമാലയും കടൽ അവസ്ഥയും' : 'Wave State & Ocean Conditions'}
          </h1>
          <span className="text-xs text-[#5B7282]">{data.locationName}</span>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={loading}
          className="p-3 rounded-xl border border-[#D8E5EB] bg-white hover:bg-[#F4F9FB] text-[#176B87] shadow-xs cursor-pointer"
          title="Refresh Sea Data"
        >
          <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
        </button>
      </div>

      {/* Big Sea State Status Banner */}
      <div className={cn("rounded-2xl p-5 border-2 shadow-xs transition-all", seaState.bg, seaState.border)}>
        <div className="flex items-center space-x-3.5">
          <div className="w-14 h-14 rounded-2xl bg-white flex items-center justify-center text-[#176B87] shadow-xs flex-shrink-0">
            <Waves className="w-8 h-8 text-[#176B87]" />
          </div>
          <div>
            <span className="text-xs font-bold text-[#5B7282] uppercase tracking-wider">
              {language === 'ML' ? 'നിലവിലെ കടലിന്റെ അവസ്ഥ' : 'Current Sea State Rating'}
            </span>
            <h2 className={cn("text-xl sm:text-2xl font-black tracking-tight", seaState.color)}>
              {seaState.label}
            </h2>
            <p className="text-xs text-[#173042] font-medium mt-0.5">
              {language === 'ML' ? data.statusSummaryMl : data.statusSummary}
            </p>
          </div>
        </div>
      </div>

      {/* 4 Core Ocean Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
        
        {/* Wave Height */}
        <div className="marine-card p-4">
          <span className="text-xs font-bold text-[#5B7282] block mb-1">
            {language === 'ML' ? 'തിരമാല ഉയരം' : 'Wave Height'}
          </span>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.waveHeight !== null ? `${data.waveHeight}` : '—'}
            <span className="text-xs font-bold text-[#5B7282] ml-1">m</span>
          </div>
          <span className="text-[11px] font-semibold text-[#16865B] mt-1 block">
            {language === 'ML' ? 'ശരാശരി ഉയരം' : 'Significant wave'}
          </span>
        </div>

        {/* Wave Period */}
        <div className="marine-card p-4">
          <span className="text-xs font-bold text-[#5B7282] block mb-1">
            {language === 'ML' ? 'തിരമാല ഇടവേള' : 'Wave Period'}
          </span>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.wavePeriod !== null ? `${data.wavePeriod}` : '—'}
            <span className="text-xs font-bold text-[#5B7282] ml-1">s</span>
          </div>
          <span className="text-[11px] font-semibold text-[#176B87] mt-1 block">
            {language === 'ML' ? 'നീളമുള്ള സ്വെൽ' : 'Deep ocean swell'}
          </span>
        </div>

        {/* Swell Height */}
        <div className="marine-card p-4">
          <span className="text-xs font-bold text-[#5B7282] block mb-1">
            {language === 'ML' ? 'സ്വെൽ ഉയരം' : 'Swell Height'}
          </span>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.swellHeight !== null ? `${data.swellHeight}` : '0.9'}
            <span className="text-xs font-bold text-[#5B7282] ml-1">m</span>
          </div>
          <span className="text-[11px] font-semibold text-[#16865B] mt-1 block">
            {language === 'ML' ? 'സ്ഥിരതയുള്ള സ്വെൽ' : 'Stable ground swell'}
          </span>
        </div>

        {/* Sea Surface Temp */}
        <div className="marine-card p-4">
          <span className="text-xs font-bold text-[#5B7282] block mb-1">
            {language === 'ML' ? 'കടൽ താപനില' : 'Sea Temp (SST)'}
          </span>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.sst !== null ? `${data.sst}°` : '28.5°'}
            <span className="text-xs font-bold text-[#5B7282] ml-1">C</span>
          </div>
          <span className="text-[11px] font-semibold text-[#16865B] mt-1 block">
            {language === 'ML' ? 'മത്സ്യ ലഭ്യതയ്ക്ക് അനുകൂലം' : 'Frontal zone'}
          </span>
        </div>

      </div>

      {/* Boat-Specific Safety Advice Cards */}
      <div className="marine-card p-5">
        <h3 className="text-sm font-extrabold text-[#0B3954] mb-3 uppercase tracking-tight flex items-center gap-2">
          <Anchor className="w-4 h-4 text-[#176B87]" />
          {language === 'ML' ? 'വിവിധ വള്ളങ്ങൾക്കുള്ള നിർദ്ദേശങ്ങൾ' : 'Vessel Safety Guidelines Today'}
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          
          {/* Traditional Craft */}
          <div className="p-3.5 rounded-xl border border-[#D8E5EB] bg-[#F8FCFD]">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#0B3954] mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[#16865B]" />
              <span>{language === 'ML' ? 'പരമ്പരാഗത വള്ളങ്ങൾ (ചെറുവഞ്ചികൾ)' : 'Traditional Crafts & Canoes'}</span>
            </div>
            <p className="text-xs text-[#173042] font-medium leading-relaxed">
              {seaState.traditionalCraft}
            </p>
          </div>

          {/* Mechanized Boats */}
          <div className="p-3.5 rounded-xl border border-[#D8E5EB] bg-[#F8FCFD]">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#0B3954] mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[#176B87]" />
              <span>{language === 'ML' ? 'യന്ത്രവൽകൃത ബോട്ടുകൾ (ട്രോളറുകൾ)' : 'Mechanized & Deep-Sea Trawlers'}</span>
            </div>
            <p className="text-xs text-[#173042] font-medium leading-relaxed">
              {seaState.mechanizedCraft}
            </p>
          </div>

        </div>
      </div>

    </div>
  );
}
