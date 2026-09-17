import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Anchor, 
  MapPin, 
  Languages, 
  PhoneCall, 
  ChevronDown, 
  Check, 
  Crosshair, 
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage, LANGUAGES, type SupportedLanguage } from '@/contexts/LanguageContext';
import { 
  COASTAL_SECTORS, 
  getNearestCoastalSector, 
  fetchLiveMarineData, 
  getSelectedLocation,
  setSelectedLocation,
  type CoastalSector 
} from '@/services/liveMarineService';

interface TopBarProps {
  onOpenCommandPalette?: () => void;
}

export default function TopBar({ onOpenCommandPalette }: TopBarProps) {
  const navigate = useNavigate();
  const { language, setLanguage, t } = useLanguage();
  
  const [selectedSector, setSelectedSector] = useState<CoastalSector>(() => {
    const loc = getSelectedLocation();
    return COASTAL_SECTORS.find(s => s.name === loc.name || (Math.abs(s.lat - loc.lat) < 0.05 && Math.abs(s.lng - loc.lng) < 0.05)) || COASTAL_SECTORS[0];
  });
  const [activeLocationLabel, setActiveLocationLabel] = useState<string>(() => {
    const loc = getSelectedLocation();
    return loc.name || COASTAL_SECTORS[0].name;
  });
  const [locationMenuOpen, setLocationMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [isDetectingGps, setIsDetectingGps] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const locationRef = useRef<HTMLDivElement>(null);
  const langRef = useRef<HTMLDivElement>(null);

  // Close menus on outside click
  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (locationRef.current && !locationRef.current.contains(e.target as Node)) {
        setLocationMenuOpen(false);
      }
      if (langRef.current && !langRef.current.contains(e.target as Node)) {
        setLangMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  // Listen to external sector changes (e.g. from map clicks)
  useEffect(() => {
    const handleExternalSectorChange = (e: any) => {
      const { lat, lng, name } = e.detail || {};
      if (name && typeof lat === 'number' && typeof lng === 'number') {
        setActiveLocationLabel(name);
        setSelectedLocation({ lat, lng, name });
        const matched = COASTAL_SECTORS.find(s => Math.abs(s.lat - lat) < 0.05 && Math.abs(s.lng - lng) < 0.05);
        if (matched) setSelectedSector(matched);
      }
    };
    window.addEventListener('marine:sector-change', handleExternalSectorChange);
    return () => window.removeEventListener('marine:sector-change', handleExternalSectorChange);
  }, []);

  const handleSelectSector = async (sector: CoastalSector) => {
    setSelectedSector(sector);
    const label = language === 'ML' ? sector.nameMl : sector.name;
    setActiveLocationLabel(label);
    setSelectedLocation({ lat: sector.lat, lng: sector.lng, name: sector.name, nameMl: sector.nameMl });
    setLocationMenuOpen(false);
    setIsRefreshing(true);
    try {
      await fetchLiveMarineData(sector.lat, sector.lng, sector.name, true);
      window.dispatchEvent(new CustomEvent('marine:sector-change', {
        detail: { lat: sector.lat, lng: sector.lng, name: sector.name }
      }));
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleGpsDetect = () => {
    if (!navigator.geolocation) return;
    setIsDetectingGps(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        const { sector, distanceKm } = getNearestCoastalSector(latitude, longitude);
        const label = distanceKm > 20 
          ? `GPS (${distanceKm}km off ${sector.name.split(' ')[0]})`
          : `GPS (${latitude.toFixed(2)}°N, ${longitude.toFixed(2)}°E)`;
        
        setActiveLocationLabel(label);
        setSelectedSector(sector);
        setSelectedLocation({ lat: latitude, lng: longitude, name: label, isGps: true });
        setIsDetectingGps(false);
        setLocationMenuOpen(false);
        setIsRefreshing(true);
        try {
          await fetchLiveMarineData(latitude, longitude, label, true);
          window.dispatchEvent(new CustomEvent('marine:sector-change', {
            detail: { lat: latitude, lng: longitude, name: label }
          }));
        } finally {
          setIsRefreshing(false);
        }
      },
      () => {
        setIsDetectingGps(false);
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  };

  return (
    <header className="h-14 md:h-16 border-b border-[#D8E5EB] bg-white sticky top-0 z-40 flex items-center justify-between px-3.5 md:px-6 shadow-sm select-none">
      
      {/* Left: Brand Identity */}
      <div className="flex items-center space-x-2.5">
        <Link to="/" className="flex items-center space-x-2 group">
          <div className="w-9 h-9 rounded-xl bg-[#0B3954] flex items-center justify-center text-white shadow-sm transition-transform group-hover:scale-105">
            <Anchor className="w-5 h-5 text-[#DFF3FA]" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-extrabold tracking-tight text-[#0B3954] leading-tight">
              {t('appName')}
            </span>
            <span className="text-[10px] font-semibold text-[#176B87] truncate leading-tight">
              {t('appTagline')}
            </span>
          </div>
        </Link>
      </div>

      {/* Center / Location Selector Pill */}
      <div className="relative" ref={locationRef}>
        <button
          type="button"
          onClick={() => setLocationMenuOpen(prev => !prev)}
          className={cn(
            "flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer",
            locationMenuOpen 
              ? "bg-[#DFF3FA] border-[#176B87] text-[#0B3954]"
              : "bg-[#F4F9FB] border-[#D8E5EB] hover:border-[#176B87] text-[#173042]"
          )}
          title={t('selectLocation')}
        >
          <MapPin className={cn("w-3.5 h-3.5 flex-shrink-0 text-[#176B87]", isRefreshing && "animate-bounce")} />
          <span className="truncate max-w-[120px] sm:max-w-[180px]">
            {activeLocationLabel}
          </span>
          <ChevronDown className={cn("w-3.5 h-3.5 text-[#5B7282] transition-transform", locationMenuOpen && "rotate-180 text-[#0B3954]")} />
        </button>

        {/* Location Dropdown Modal */}
        {locationMenuOpen && (
          <div className="absolute left-1/2 -translate-x-1/2 sm:left-0 sm:translate-x-0 top-full mt-2 w-72 sm:w-80 bg-white border border-[#C4D9E2] rounded-2xl shadow-xl z-50 p-2.5 text-[#173042] animate-in fade-in zoom-in-95 duration-150">
            {/* GPS Button */}
            <button
              type="button"
              onClick={handleGpsDetect}
              disabled={isDetectingGps}
              className="w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-xl bg-[#DFF3FA] hover:bg-[#D4EEF7] text-[#0B3954] font-semibold text-xs transition-colors cursor-pointer"
            >
              {isDetectingGps ? (
                <Loader2 className="w-4 h-4 animate-spin text-[#176B87]" />
              ) : (
                <Crosshair className="w-4 h-4 text-[#176B87]" />
              )}
              <div className="flex flex-col text-left">
                <span>{isDetectingGps ? 'Locating...' : t('useGps')}</span>
                <span className="text-[10px] text-[#5B7282] font-normal">GPS coordinates</span>
              </div>
            </button>

            <div className="my-2 border-t border-[#E2EDF2]" />

            <div className="text-[11px] font-bold text-[#5B7282] px-2 py-1 uppercase tracking-wider">
              {t('selectLocation')}
            </div>

            <div className="max-h-56 overflow-y-auto space-y-1 scrollbar-thin">
              {COASTAL_SECTORS.map((sector) => {
                const isSelected = selectedSector.id === sector.id;
                const label = language === 'ML' ? sector.nameMl : sector.name;
                return (
                  <button
                    key={sector.id}
                    type="button"
                    onClick={() => handleSelectSector(sector)}
                    className={cn(
                      "w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-left text-xs font-medium transition-colors cursor-pointer",
                      isSelected 
                        ? "bg-[#DFF3FA] text-[#0B3954] font-bold"
                        : "hover:bg-[#F4F9FB] text-[#173042]"
                    )}
                  >
                    <div className="flex flex-col min-w-0 pr-2">
                      <span className="truncate">{label}</span>
                      <span className="text-[10px] text-[#5B7282]">{sector.region}</span>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-[#16865B] flex-shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Right: Language Selector & Emergency SOS */}
      <div className="flex items-center space-x-2">
        
        {/* Language Selector */}
        <div className="relative" ref={langRef}>
          <button
            type="button"
            onClick={() => setLangMenuOpen(prev => !prev)}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl border border-[#D8E5EB] bg-white hover:bg-[#F4F9FB] text-xs font-bold text-[#0B3954] transition-colors cursor-pointer shadow-xs"
            title="Change Language"
          >
            <Languages className="w-3.5 h-3.5 text-[#176B87]" />
            <span>{LANGUAGES.find(l => l.code === language)?.nativeName || 'Language'}</span>
            <ChevronDown className="w-3 h-3 text-[#5B7282]" />
          </button>

          {langMenuOpen && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-[#C4D9E2] rounded-2xl shadow-xl z-50 p-1.5 text-[#173042] animate-in fade-in zoom-in-95 duration-150">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => {
                    setLanguage(lang.code);
                    setLangMenuOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-xs font-medium transition-colors cursor-pointer",
                    language === lang.code
                      ? "bg-[#DFF3FA] text-[#0B3954] font-bold"
                      : "hover:bg-[#F4F9FB] text-[#173042]"
                  )}
                >
                  <div className="flex flex-col">
                    <span className="text-xs">{lang.nativeName}</span>
                    <span className="text-[10px] text-[#5B7282]">{lang.name}</span>
                  </div>
                  {language === lang.code && <Check className="w-4 h-4 text-[#16865B]" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Emergency SOS Call (High-Visibility Red Badge) */}
        <a
          href="tel:112"
          className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-[#FDF0EE] hover:bg-[#FCE8E5] border border-[#F5B8B1] rounded-xl text-[#C0392B] text-xs font-bold transition-all shadow-xs"
          title="Emergency Help 112"
        >
          <PhoneCall className="w-3.5 h-3.5 text-[#C0392B] animate-pulse" />
          <span className="hidden xs:inline">112</span>
        </a>
      </div>
    </header>
  );
}
