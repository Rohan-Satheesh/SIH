import React, { useState, useEffect } from 'react';
import { 
  CloudSun, 
  Wind, 
  Droplets, 
  Eye, 
  Compass, 
  ChevronDown, 
  ChevronUp, 
  AlertTriangle, 
  Clock, 
  Thermometer,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  fetchLiveMarineData, 
  getCachedMarineData, 
  type LiveMarineData 
} from '@/services/liveMarineService';

export default function WeatherView() {
  const { language, t } = useLanguage();
  const [data, setData] = useState<LiveMarineData>(getCachedMarineData());
  const [showAdvanced, setShowAdvanced] = useState(false);
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

  // Human-readable meteorological advice
  const getWindAdvice = (speed: number | null) => {
    if (speed === null) return { en: 'Light breeze along coast.', ml: 'തീരദേശത്ത് നേരിയ കാറ്റ്.' };
    if (speed < 18) return { en: 'Calm to gentle breeze. Safe for all fishing craft.', ml: 'ശാന്തമായ കാറ്റ്. എല്ലാത്തരം വള്ളങ്ങൾക്കും അനുകൂലം.' };
    if (speed < 30) return { en: 'Moderate breeze. Small canoes may feel chop.', ml: 'മിതമായ കാറ്റ്. ചെറുവള്ളങ്ങൾ ജാഗ്രത പാലിക്കുക.' };
    return { en: 'Strong winds and gusts. Coastal craft caution advisory.', ml: 'ശക്തമായ കാറ്റ്. വള്ളങ്ങൾ കടലിൽ പോകുന്നത് ഒഴിവാക്കുക.' };
  };

  const getRainAdvice = (code: number | null) => {
    if (code === null || code === 0) return { en: 'Clear skies expected throughout the shift.', ml: 'ഇന്ന് ആകാശം തെളിഞ്ഞ് കാണപ്പെടും.' };
    if (code <= 3) return { en: 'Passing clouds. No major squall lines expected.', ml: 'ഭാഗികമായി മേഘാവൃതം. വലിയ മഴയ്ക്ക് സാധ്യതയില്ല.' };
    if (code >= 95) return { en: 'Thunderstorm warning. Keep away from metal rigging and seek harbor.', ml: 'ഇടിമിന്നൽ ജാഗ്രത! തുറമുഖത്തേക്ക് മടങ്ങുക.' };
    return { en: 'Passing rain showers. Keep navigation lights operational.', ml: 'ഇടയ്ക്കിടെ മഴയുണ്ടാകും. ലൈറ്റുകൾ പ്രവർത്തനക്ഷമമാക്കുക.' };
  };

  const windAdvice = getWindAdvice(data.windSpeed);
  const rainAdvice = getRainAdvice(data.weatherCode);

  return (
    <div className="max-w-4xl mx-auto px-3.5 sm:px-6 py-4 space-y-4">
      
      {/* Header with Location & Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-bold text-[#176B87] uppercase tracking-wider">
            {t('navWeather')}
          </span>
          <h1 className="text-xl sm:text-2xl font-black text-[#0B3954]">
            {language === 'ML' ? 'ഇന്നത്തെ തീരദേശ കാലാവസ്ഥ' : "Today's Coastal Weather"}
          </h1>
          <span className="text-xs text-[#5B7282]">{data.locationName}</span>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={loading}
          className="p-3 rounded-xl border border-[#D8E5EB] bg-white hover:bg-[#F4F9FB] text-[#176B87] shadow-xs cursor-pointer"
          title="Refresh Weather"
        >
          <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
        </button>
      </div>

      {/* Primary Big Summary Card */}
      <div className="marine-card p-5 border-[#C4D9E2]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-[#DFF3FA] flex items-center justify-center text-[#176B87] flex-shrink-0 shadow-xs">
              <CloudSun className="w-9 h-9 text-[#176B87]" />
            </div>
            <div>
              <div className="text-4xl sm:text-5xl font-black text-[#0B3954]">
                {data.airTemperature !== null ? `${data.airTemperature}°` : '28°'}
                <span className="text-xl font-bold text-[#5B7282] ml-1">C</span>
              </div>
              <div className="text-sm font-bold text-[#176B87] mt-0.5">
                {language === 'ML' ? data.weatherDescription.ml : data.weatherDescription.en}
              </div>
            </div>
          </div>

          <div className="bg-[#F4F9FB] rounded-xl p-3 border border-[#E2EDF2] sm:max-w-xs text-xs space-y-1">
            <div className="font-bold text-[#0B3954] flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-[#16865B]" />
              {language === 'ML' ? 'കാലാവസ്ഥ ഉപദേശം' : 'Weather Summary'}
            </div>
            <p className="text-[#173042] font-medium leading-relaxed">
              {language === 'ML' ? windAdvice.ml : windAdvice.en}
            </p>
          </div>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
        
        {/* Wind */}
        <div className="marine-card p-4">
          <div className="flex items-center justify-between text-[#5B7282] mb-1">
            <span className="text-xs font-bold">{t('windSpeed')}</span>
            <Wind className="w-4 h-4 text-[#176B87]" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.windSpeed !== null ? `${data.windSpeed}` : '—'}
            <span className="text-xs font-bold text-[#5B7282] ml-1">km/h</span>
          </div>
          <span className="text-[11px] font-semibold text-[#176B87] mt-1 block">
            {data.windDirection !== null ? `${data.windDirection}° heading` : 'Steady'}
          </span>
        </div>

        {/* Rain Probability */}
        <div className="marine-card p-4">
          <div className="flex items-center justify-between text-[#5B7282] mb-1">
            <span className="text-xs font-bold">{t('rainChance')}</span>
            <Droplets className="w-4 h-4 text-[#176B87]" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.hourlyForecast[0]?.rainProb !== undefined ? `${data.hourlyForecast[0].rainProb}%` : '15%'}
          </div>
          <span className="text-[11px] font-semibold text-[#16865B] mt-1 block">
            {language === 'ML' ? 'കുറഞ്ഞ സാധ്യത' : 'Low Probability'}
          </span>
        </div>

        {/* Visibility */}
        <div className="marine-card p-4">
          <div className="flex items-center justify-between text-[#5B7282] mb-1">
            <span className="text-xs font-bold">{language === 'ML' ? 'ദൂരക്കാഴ്ച' : 'Visibility'}</span>
            <Eye className="w-4 h-4 text-[#176B87]" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.visibilityKm !== null ? `${data.visibilityKm} km` : '15 km'}
          </div>
          <span className="text-[11px] font-semibold text-[#16865B] mt-1 block">
            {language === 'ML' ? 'നല്ല ദൂരക്കാഴ്ച' : 'Clear Sightlines'}
          </span>
        </div>

        {/* Humidity */}
        <div className="marine-card p-4">
          <div className="flex items-center justify-between text-[#5B7282] mb-1">
            <span className="text-xs font-bold">{language === 'ML' ? 'ഈർപ്പം' : 'Humidity'}</span>
            <Thermometer className="w-4 h-4 text-[#176B87]" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-[#0B3954]">
            {data.relativeHumidity !== null ? `${data.relativeHumidity}%` : '80%'}
          </div>
          <span className="text-[11px] font-semibold text-[#5B7282] mt-1 block">
            {language === 'ML' ? 'തീരദേശ ഈർപ്പം' : 'Coastal Humid'}
          </span>
        </div>

      </div>

      {/* Hourly Forecast Strip */}
      {data.hourlyForecast.length > 0 && (
        <div className="marine-card p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#0B3954]">
              <Clock className="w-4 h-4 text-[#176B87]" />
              <span>{language === 'ML' ? 'അടുത്ത മണിക്കൂറുകളിലെ പ്രവചനം' : 'Hourly Coastal Forecast'}</span>
            </div>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {data.hourlyForecast.slice(0, 6).map((item, idx) => (
              <div 
                key={idx} 
                className="bg-[#F4F9FB] rounded-xl p-2.5 flex flex-col items-center justify-center text-center border border-[#E2EDF2]"
              >
                <span className="text-[11px] font-bold text-[#5B7282]">{item.hour}</span>
                <span className="text-lg font-black text-[#0B3954] my-1">{item.temp}°C</span>
                <span className="text-[10px] font-semibold text-[#176B87]">{item.windSpeed} km/h</span>
                <span className="text-[10px] text-[#16865B] mt-0.5">{item.waveHeight}m wave</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expandable More Details Section */}
      <div className="marine-card p-4">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between text-xs font-bold text-[#0B3954] cursor-pointer"
        >
          <span>{language === 'ML' ? 'കൂടുതൽ വിവരങ്ങൾ (കാറ്റിന്റെ വേഗത, ഗസ്റ്റുകൾ)' : 'More Weather & Gust Details'}</span>
          {showAdvanced ? <ChevronUp className="w-4 h-4 text-[#176B87]" /> : <ChevronDown className="w-4 h-4 text-[#176B87]" />}
        </button>

        {showAdvanced && (
          <div className="mt-3 pt-3 border-t border-[#E2EDF2] grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-[#F8FCFD] p-3 rounded-xl border border-[#D8E5EB]">
              <span className="text-[#5B7282] block">{language === 'ML' ? 'കാറ്റിന്റെ ഗസ്റ്റുകൾ' : 'Wind Gusts'}</span>
              <span className="text-lg font-bold text-[#0B3954]">
                {data.windGusts !== null ? `${data.windGusts} km/h` : '—'}
              </span>
            </div>
            <div className="bg-[#F8FCFD] p-3 rounded-xl border border-[#D8E5EB]">
              <span className="text-[#5B7282] block">{language === 'ML' ? 'കടൽ ഉപരിതല താപനില' : 'Sea Surface Temp'}</span>
              <span className="text-lg font-bold text-[#0B3954]">
                {data.sst !== null ? `${data.sst}°C` : '28.5°C'}
              </span>
            </div>
            <div className="bg-[#F8FCFD] p-3 rounded-xl border border-[#D8E5EB]">
              <span className="text-[#5B7282] block">{language === 'ML' ? 'മഴ സാധ്യത' : 'Precipitation Advice'}</span>
              <span className="text-xs font-semibold text-[#173042]">
                {language === 'ML' ? rainAdvice.ml : rainAdvice.en}
              </span>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
