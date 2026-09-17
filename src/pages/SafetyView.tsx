import React, { useState, useEffect } from 'react';
import { 
  AlertOctagon, 
  PhoneCall, 
  ShieldAlert, 
  LifeBuoy, 
  CheckSquare, 
  Square, 
  MapPin, 
  Radio, 
  Copy, 
  Check, 
  Navigation, 
  Compass, 
  AlertTriangle, 
  Info 
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { fetchLiveMarineData, COASTAL_SECTORS } from '../services/liveMarineService';

import { getSelectedLocation } from '@/services/liveMarineService';

export function SafetyView() {
  const { language, t } = useLanguage();
  const [copiedCoords, setCopiedCoords] = useState(false);
  const [currentCoords, setCurrentCoords] = useState(() => {
    const loc = getSelectedLocation();
    return { lat: loc.lat, lng: loc.lng, sectorName: loc.name };
  });

  useEffect(() => {
    const handleSectorChange = (e: any) => {
      const { lat, lng, name } = e.detail || {};
      if (typeof lat === 'number' && typeof lng === 'number') {
        setCurrentCoords({ lat, lng, sectorName: name || `${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E` });
      }
    };
    window.addEventListener('marine:sector-change', handleSectorChange);
    return () => window.removeEventListener('marine:sector-change', handleSectorChange);
  }, []);

  // Checklist items
  const [checklist, setChecklist] = useState<Record<string, boolean>>({
    lifejackets: true,
    vhfRadio: true,
    gpsCompass: false,
    freshWater: true,
    batteryPhone: true,
    familyNotified: false
  });

  const toggleCheck = (id: string) => {
    setChecklist(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const completedCount = Object.values(checklist).filter(Boolean).length;
  const totalChecklist = Object.keys(checklist).length;

  const handleCopyCoords = () => {
    const coordStr = `${currentCoords.lat.toFixed(4)}° N, ${currentCoords.lng.toFixed(4)}° E (${currentCoords.sectorName})`;
    navigator.clipboard.writeText(coordStr);
    setCopiedCoords(true);
    setTimeout(() => setCopiedCoords(false), 2500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 pb-12">
      {/* Critical Emergency Banner */}
      <div className="bg-[#FDEDEC] border-2 border-[#C0392B] rounded-2xl p-4 md:p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-[#C0392B] text-white flex items-center justify-center shrink-0 animate-pulse">
              <AlertOctagon className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-black text-[#C0392B] tracking-tight">
                {language === 'ML' ? 'അടിയന്തര സഹായം & SOS' : 'Emergency SOS & Safety'}
              </h1>
              <p className="text-xs md:text-sm font-medium text-[#173042]">
                {language === 'ML' 
                  ? 'അടിയന്തര ഘട്ടങ്ങളിൽ താഴെയുള്ള നമ്പറുകളിൽ നേരിട്ട് വിളിക്കാം' 
                  : 'Instant 1-tap direct dialers for maritime search & rescue'}
              </p>
            </div>
          </div>
        </div>

        {/* Current GPS Coordinates Card */}
        <div className="mt-4 bg-white rounded-xl p-3.5 border border-[#EAA29A] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <MapPin className="w-5 h-5 text-[#C0392B] shrink-0" />
            <div>
              <span className="text-xs text-[#52798F] block font-medium">
                {language === 'ML' ? 'നിങ്ങളുടെ നിലവിലെ ബോട്ട് സ്ഥാനം (Vessel Coords):' : 'Current Vessel Coordinates:'}
              </span>
              <span className="text-base md:text-lg font-bold text-[#0B3954] tracking-wide font-mono">
                {currentCoords.lat.toFixed(4)}° N, {currentCoords.lng.toFixed(4)}° E
              </span>
              <span className="text-xs text-[#52798F] ml-2">({currentCoords.sectorName})</span>
            </div>
          </div>

          <button
            onClick={handleCopyCoords}
            className="h-10 px-3.5 bg-[#F4FAFC] hover:bg-[#DFF3FA] border border-[#D2E6ED] text-[#0B3954] text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-colors self-start sm:self-auto"
          >
            {copiedCoords ? <Check className="w-4 h-4 text-[#16865B]" /> : <Copy className="w-4 h-4 text-[#176B87]" />}
            <span>{copiedCoords ? (language === 'ML' ? 'കോപ്പി ചെയ്തു!' : 'Copied!') : (language === 'ML' ? 'കോപ്പി ചെയ്യുക' : 'Copy Coordinates')}</span>
          </button>
        </div>
      </div>

      {/* 1-TAP EMERGENCY CALL BUTTONS (High Sunlight Visibility, Huge Touch Targets) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {/* National Emergency 112 */}
        <a
          href="tel:112"
          className="bg-[#C0392B] hover:bg-[#A93226] text-white rounded-2xl p-4.5 flex items-center justify-between shadow-md transition-all active:scale-[0.98] min-h-[72px]"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-white shrink-0">
              <PhoneCall className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-white/80 block">
                {language === 'ML' ? 'ദേശീയ അടിയന്തര നമ്പർ' : 'National Emergency Service'}
              </span>
              <span className="text-2xl font-black tracking-tight">112</span>
            </div>
          </div>
          <span className="bg-white text-[#C0392B] font-bold text-xs px-3 py-1.5 rounded-full uppercase tracking-wider shadow-xs">
            {language === 'ML' ? 'വിളിക്കുക' : 'Call Now'}
          </span>
        </a>

        {/* Indian Coast Guard SAR 1554 */}
        <a
          href="tel:1554"
          className="bg-[#0B3954] hover:bg-[#176B87] text-white rounded-2xl p-4.5 flex items-center justify-between shadow-md transition-all active:scale-[0.98] min-h-[72px]"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-white shrink-0">
              <LifeBuoy className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-white/80 block">
                {language === 'ML' ? 'ഇന്ത്യൻ കോസ്റ്റ് ഗാർഡ് SAR' : 'Indian Coast Guard SAR'}
              </span>
              <span className="text-2xl font-black tracking-tight">1554</span>
            </div>
          </div>
          <span className="bg-[#DFF3FA] text-[#0B3954] font-bold text-xs px-3 py-1.5 rounded-full uppercase tracking-wider shadow-xs">
            {language === 'ML' ? 'വിളിക്കുക' : 'Call Now'}
          </span>
        </a>

        {/* Coastal Marine Police 1093 */}
        <a
          href="tel:1093"
          className="bg-white hover:bg-[#F4FAFC] border-2 border-[#176B87] text-[#0B3954] rounded-2xl p-4 flex items-center justify-between shadow-xs transition-all active:scale-[0.98] min-h-[64px]"
        >
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-[#DFF3FA] flex items-center justify-center text-[#176B87] shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-medium text-[#52798F] block">
                {language === 'ML' ? 'കോസ്റ്റൽ മറൈൻ പോലീസ്' : 'Coastal Marine Police'}
              </span>
              <span className="text-xl font-bold text-[#0B3954]">1093</span>
            </div>
          </div>
          <span className="bg-[#176B87] text-white font-bold text-xs px-3 py-1.5 rounded-full">
            {language === 'ML' ? 'വിളിക്കുക' : 'Call'}
          </span>
        </a>

        {/* Fisheries Department Distress */}
        <a
          href="tel:18004251660"
          className="bg-white hover:bg-[#F4FAFC] border-2 border-[#D2E6ED] text-[#0B3954] rounded-2xl p-4 flex items-center justify-between shadow-xs transition-all active:scale-[0.98] min-h-[64px]"
        >
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-[#D9F3E6] flex items-center justify-center text-[#16865B] shrink-0">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-medium text-[#52798F] block">
                {language === 'ML' ? 'ഫിഷറീസ് വകുപ്പ് ഹെൽപ്പ്‌ലൈൻ' : 'Fisheries Toll-Free Control'}
              </span>
              <span className="text-lg font-bold text-[#0B3954]">1800-425-1660</span>
            </div>
          </div>
          <span className="bg-[#16865B] text-white font-bold text-xs px-3 py-1.5 rounded-full">
            {language === 'ML' ? 'വിളിക്കുക' : 'Call'}
          </span>
        </a>
      </div>

      {/* Geofence & Maritime Boundary Status */}
      <div className="bg-white border border-[#D2E6ED] rounded-2xl p-4 shadow-xs">
        <div className="flex items-center gap-2 mb-2">
          <Navigation className="w-5 h-5 text-[#176B87]" />
          <h2 className="text-base font-bold text-[#0B3954]">
            {language === 'ML' ? 'അതിർത്തി & ജിയോഫെൻസ് പരിശോധന' : 'Maritime Border & Geofence Status'}
          </h2>
        </div>
        <div className="p-3 bg-[#D9F3E6] border border-[#B3E5CD] rounded-xl flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-[#16865B] shrink-0 mt-0.5" />
          <div className="text-xs text-[#173042] space-y-1">
            <span className="font-bold text-[#16865B] block text-sm">
              {language === 'ML' ? 'നിങ്ങൾ ഇന്ത്യൻ സമുദ്ര പരിധിയിലാണ് (Safe Zone)' : 'Inside Indian Exclusive Economic Zone (Safe Zone)'}
            </span>
            <p>
              {language === 'ML'
                ? 'അന്താരാഷ്ട്ര സമുദ്ര അതിർത്തിയിൽ (IMBL) നിന്നും 148 നോട്ടിക്കൽ മൈൽ അകലെയാണ്. അന്താരാഷ്ട്ര അതിർത്തി ലംഘിക്കാനുള്ള സാധ്യതയില്ല.'
                : 'Current position is 148 Nautical Miles clear of international maritime boundary lines (IMBL). No border violations detected.'}
            </p>
          </div>
        </div>
      </div>

      {/* PRE-DEPARTURE SAFETY CHECKLIST */}
      <div className="bg-white border border-[#D2E6ED] rounded-2xl p-4 md:p-5 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base md:text-lg font-bold text-[#0B3954]">
              {language === 'ML' ? 'യാത്രയ്ക്ക് മുമ്പുള്ള സുരക്ഷാ പരിശോധന' : 'Pre-Departure Safety Checklist'}
            </h2>
            <p className="text-xs text-[#52798F]">
              {language === 'ML' 
                ? 'കടലിലേക്ക് തിരിക്കുന്നതിന് മുൻപ് ഓരോ ഇനവും പരിശോധിച്ച് ഉറപ്പുവരുത്തുക' 
                : 'Verify every safety requirement prior to leaving the harbor'}
            </p>
          </div>
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
            completedCount === totalChecklist 
              ? 'bg-[#D9F3E6] text-[#16865B]' 
              : 'bg-[#FFF7E6] text-[#D99116]'
          }`}>
            {completedCount} / {totalChecklist} {language === 'ML' ? 'പൂർത്തിയായി' : 'Ready'}
          </span>
        </div>

        <div className="space-y-2.5 pt-1">
          {[
            {
              id: 'lifejackets',
              titleMl: 'എല്ലാ തൊഴിലാളികൾക്കും ലൈഫ് ജാക്കറ്റ് ലഭ്യമാണ്',
              titleEn: 'Life jackets available for all crew members on board',
              subMl: 'ഓരോ തൊഴിലാളിയും ലൈഫ് ജാക്കറ്റ് ധരിച്ചിട്ടുണ്ടെന്ന് ഉറപ്പാക്കുക.',
              subEn: 'Ensure every crew member wears and fastens their life jacket.'
            },
            {
              id: 'vhfRadio',
              titleMl: 'VHF വയർലെസ് റേഡിയോ (ചാനൽ 16) പ്രവർത്തനക്ഷമം',
              titleEn: 'VHF Marine Radio working on emergency Channel 16',
              subMl: 'തീരദേശ കൺട്രോൾ റൂമുമായി റേഡിയോ ചെക്ക് നടത്തുക.',
              subEn: 'Conduct a radio check with shore station or nearby boats.'
            },
            {
              id: 'gpsCompass',
              titleMl: 'ജിപിഎസ് നാവിഗേഷൻ / കാന്തിക കോമ്പസ്',
              titleEn: 'GPS navigation device & magnetic compass operational',
              subMl: 'ബാക്കപ്പ് ബാറ്ററി ഉണ്ടെന്ന് ഉറപ്പുവരുത്തുക.',
              subEn: 'Ensure secondary battery backup is charged.'
            },
            {
              id: 'freshWater',
              titleMl: 'കുടിവെള്ളവും 20% അധിക ഡീസൽ കരുതലും',
              titleEn: 'Sufficient fresh water & +20% reserve diesel fuel',
              subMl: 'പ്രതീക്ഷിക്കാത്ത കാലാവസ്ഥാ തടസ്സങ്ങൾക്കായി കരുതൽ ഇന്ധനം സൂക്ഷിക്കുക.',
              subEn: 'Reserve fuel prevents stranding during sudden sea currents.'
            },
            {
              id: 'batteryPhone',
              titleMl: 'മൊബൈൽ ഫോൺ ഫുൾ ചാർജ് + വാട്ടർപ്രൂഫ് പൗച്ച്',
              titleEn: 'Mobile phones charged and secured in waterproof pouches',
              subMl: 'നനവ് തട്ടാതെ സൂക്ഷിക്കുക.',
              subEn: 'Keep phone dry and accessible for emergency SOS calls.'
            },
            {
              id: 'familyNotified',
              titleMl: 'തിരിച്ചെത്തുന്ന സമയം കുടുംബത്തെയോ ഹാർബറിലോ അറിയിച്ചു',
              titleEn: 'Float plan and return time communicated with family/harbor',
              subMl: 'പോകുന്ന ദിശയും ആളുകളുടെ എണ്ണവും രേഖപ്പെടുത്തുക.',
              subEn: 'Record boat number, destination sector, and estimated return.'
            }
          ].map((item) => {
            const isChecked = checklist[item.id];
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => toggleCheck(item.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-start gap-3.5 ${
                  isChecked
                    ? 'bg-[#F4FAFC] border-[#BDE0EE]'
                    : 'bg-white border-[#D2E6ED] hover:bg-[#F8FCFD]'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isChecked ? (
                    <CheckSquare className="w-5 h-5 text-[#16865B]" />
                  ) : (
                    <Square className="w-5 h-5 text-[#52798F]" />
                  )}
                </div>
                <div className="flex-1">
                  <span className={`text-sm font-bold block ${isChecked ? 'text-[#0B3954]' : 'text-[#173042]'}`}>
                    {language === 'ML' ? item.titleMl : item.titleEn}
                  </span>
                  <span className="text-xs text-[#52798F] block mt-0.5">
                    {language === 'ML' ? item.subMl : item.subEn}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* VHF Radio Guidelines Note */}
      <div className="bg-[#FFF7E6] border border-[#F2D184] rounded-2xl p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-[#D99116] shrink-0 mt-0.5" />
        <div className="text-xs text-[#173042]">
          <span className="font-bold text-[#D99116] block mb-1">
            {language === 'ML' ? 'VHF എമർജൻസി കോൾ മാർഗ്ഗനിർദ്ദേശം (MAYDAY)' : 'VHF Distress Procedure (MAYDAY)'}
          </span>
          <p className="leading-relaxed">
            {language === 'ML'
              ? 'ഗുരുതരമായ അപകട ഘട്ടങ്ങളിൽ ചാനൽ 16-ൽ "MAYDAY, MAYDAY, MAYDAY" എന്ന് മൂന്ന് തവണ പറയുക. തുടർന്ന് ബോട്ടിന്റെ പേര്, രജിസ്ട്രേഷൻ നമ്പർ, ജിപിഎസ് സ്ഥാനം (അക്ഷാംശം & രേഖാംശം), ബോട്ടിലുള്ള ആളുകളുടെ എണ്ണം എന്നിവ വ്യക്തമായി അറിയിക്കുക.'
              : 'In life-threatening situations, transmit on Channel 16: "MAYDAY, MAYDAY, MAYDAY". State your vessel registration, GPS coordinates, nature of distress, and number of souls on board.'}
          </p>
        </div>
      </div>
    </div>
  );
}
