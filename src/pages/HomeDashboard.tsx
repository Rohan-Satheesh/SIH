import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  AlertTriangle, 
  AlertOctagon, 
  Waves, 
  Wind, 
  CloudSun, 
  Fish, 
  MessageSquare, 
  PhoneCall, 
  ArrowRight, 
  Clock, 
  MapPin, 
  Compass,
  RefreshCw,
  Thermometer
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  fetchLiveMarineData, 
  getCachedMarineData, 
  type LiveMarineData 
} from '@/services/liveMarineService';

export default function HomeDashboard() {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  
  const [data, setData] = useState<LiveMarineData>(getCachedMarineData());
  const [loading, setLoading] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const loadData = async (force: boolean = false) => {
    setLoading(true);
    try {
      const res = await fetchLiveMarineData(data.latitude, data.longitude, data.locationName, force);
      setData(res);
      const now = new Date();
      setLastRefreshed(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Listen for coordinate changes from topbar or map
    const handleSectorChange = (e: any) => {
      const { lat, lng, name } = e.detail || {};
      if (lat && lng) {
        fetchLiveMarineData(lat, lng, name, true).then((res) => {
          setData(res);
          const now = new Date();
          setLastRefreshed(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        });
      }
    };

    window.addEventListener('marine:sector-change', handleSectorChange);
    return () => window.removeEventListener('marine:sector-change', handleSectorChange);
  }, []);

  // Today's greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (language === 'ML') {
      if (hour < 12) return 'സുപ്രഭാതം!';
      if (hour < 17) return 'ശുഭദിനം!';
      return 'ശുഭസായാഹ്നം!';
    }
    if (hour < 12) return 'Good Morning!';
    if (hour < 17) return 'Good Afternoon!';
    return 'Good Evening!';
  };

  // Formatted safety explanation
  const getSafetyDetails = () => {
    const isSafe = data.riskLevel === 'LOW';
    const isCaution = data.riskLevel === 'MEDIUM' || data.riskLevel === 'HIGH';
    
    if (isSafe) {
      return {
        badge: language === 'ML' ? 'കടലിൽ പോകാൻ സുരക്ഷിതം' : 'SAFE FOR FISHING',
        badgeClass: 'status-badge-safe',
        icon: ShieldCheck,
        iconColor: 'text-[#16865B]',
        bgColor: 'bg-[#E8F7F0]',
        borderColor: 'border-[#A6E2C6]',
        description: language === 'ML'
          ? `തിരമാലകൾ ${data.waveHeight ?? 1.2} മീറ്റർ മാത്രം. കാറ്റിന്റെ വേഗത ${data.windSpeed ?? 14} കി.മീ/മണിക്കൂർ. ഇന്നത്തെ കടൽാവസ്ഥ സുരക്ഷിതമാണ്.`
          : `Wave height is ${data.waveHeight ?? 1.2}m. Wind speed is ${data.windSpeed ?? 14} km/h. Sea conditions are calm and favorable for fishing.`,
      };
    }

    if (isCaution) {
      return {
        badge: language === 'ML' ? 'ജാഗ്രത പാലിക്കുക' : 'CAUTION ADVISED',
        badgeClass: 'status-badge-warning',
        icon: AlertTriangle,
        iconColor: 'text-[#D99116]',
        bgColor: 'bg-[#FEF6E8]',
        borderColor: 'border-[#F8DAA5]',
        description: language === 'ML'
          ? `തിരമാലകൾ ${data.waveHeight ?? 1.8} മീറ്ററാണ്. കാറ്റിന്റെ വേഗത ${data.windSpeed ?? 26} കി.മീ/മണിക്കൂർ. ചെറുവള്ളങ്ങൾ തീരത്തോടടുത്ത് നിൽക്കുക.`
          : `Moderate waves at ${data.waveHeight ?? 1.8}m and winds at ${data.windSpeed ?? 26} km/h. Small crafts should exercise caution and avoid deep waters.`,
      };
    }

    return {
      badge: language === 'ML' ? 'അപകടകരം - കടലിൽ പോകരുത്!' : 'DANGER - DO NOT VENTURE OUT',
      badgeClass: 'status-badge-danger',
      icon: AlertOctagon,
      iconColor: 'text-[#C0392B]',
      bgColor: 'bg-[#FDF0EE]',
      borderColor: 'border-[#F5B8B1]',
      description: language === 'ML'
        ? `അതിശക്തമായ കാറ്റും ഉയർന്ന തിരമാലകളും (${data.waveHeight ?? 3.2}m). ആരും കടലിൽ പോകരുത്. തീരദേശ ജാഗ്രതാ നിർദ്ദേശം നിലവിലുണ്ട്.`
        : `Rough sea conditions with high waves (${data.waveHeight ?? 3.2}m) and strong gale winds. Marine craft advisory in effect. Stay ashore.`,
    };
  };

  const safety = getSafetyDetails();
  const SafetyIcon = safety.icon;

  const formattedDate = new Date().toLocaleDateString(language === 'ML' ? 'ml-IN' : 'en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });

  return (
    <div className="max-w-4xl mx-auto px-3.5 sm:px-6 py-4 space-y-4">
      
      {/* 1. Hero Friendly Greeting Banner */}
      <section className="marine-card p-4 sm:p-5 border-[#C4D9E2]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2 text-xs text-[#176B87] font-bold">
              <Clock className="w-3.5 h-3.5" />
              <span>{formattedDate}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3 text-[#176B87]" />
                {data.locationName}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-[#0B3954] mt-0.5 tracking-tight">
              {getGreeting()} {language === 'ML' ? 'സുഹൃത്തേ' : 'Friend'}
            </h1>
            <p className="text-sm text-[#5B7282] mt-0.5">
              {language === 'ML' 
                ? 'ഇന്നത്തെ കടൽ, കാലാവസ്ഥ, മീൻപിടുത്ത സാധ്യതകൾ ഒറ്റനോട്ടത്തിൽ' 
                : "Today's marine weather, sea conditions, and fishing zones at a glance"}
            </p>
          </div>

          <div className="flex items-center space-x-2 self-start sm:self-center">
            <button
              type="button"
              onClick={() => loadData(true)}
              disabled={loading}
              className="p-3 rounded-xl border border-[#D8E5EB] bg-white hover:bg-[#F4F9FB] text-[#176B87] transition-all cursor-pointer shadow-xs"
              title="Refresh Live Data"
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
            </button>
          </div>
        </div>
      </section>

      {/* 2. Primary Safety Verdict: "Is it safe to go fishing today?" */}
      <section className={cn("rounded-2xl p-4 sm:p-5 border-2 shadow-sm transition-all", safety.bgColor, safety.borderColor)}>
        <div className="flex items-start space-x-3.5">
          <div className={cn("w-12 h-12 rounded-2xl bg-white shadow-xs flex items-center justify-center flex-shrink-0 border", safety.borderColor)}>
            <SafetyIcon className={cn("w-7 h-7", safety.iconColor)} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="text-[11px] font-bold text-[#5B7282] uppercase tracking-wider">
              {t('todayVerdict')}
            </div>
            <h2 className={cn("text-lg sm:text-xl font-extrabold tracking-tight mt-0.5", safety.iconColor)}>
              {safety.badge}
            </h2>
            <p className="text-sm font-medium text-[#173042] mt-1.5 leading-relaxed">
              {safety.description}
            </p>

            <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-black/5">
              <button
                type="button"
                onClick={() => navigate('/sea')}
                className="touch-btn bg-white hover:bg-slate-50 border border-[#D8E5EB] text-xs text-[#0B3954] shadow-xs font-bold gap-1.5"
              >
                <span>{language === 'ML' ? 'തിരമാല നില കാണുക' : 'View Wave State'}</span>
                <ArrowRight className="w-3.5 h-3.5 text-[#176B87]" />
              </button>

              <button
                type="button"
                onClick={() => navigate('/zones')}
                className="touch-btn bg-[#0B3954] hover:bg-[#176B87] text-white text-xs shadow-xs font-bold gap-1.5"
              >
                <span>{language === 'ML' ? 'മീൻപിടുത്ത മേഖലകൾ' : 'Best Fishing Zones'}</span>
                <ArrowRight className="w-3.5 h-3.5 text-white" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Quick Status Cards Grid (4 Big Sunlight-Readable Cards) */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-extrabold text-[#0B3954] tracking-tight uppercase">
            {language === 'ML' ? 'ഇന്നത്തെ കടൽ വിവരങ്ങൾ' : 'Current Sea Telemetry'}
          </h3>
          {lastRefreshed && (
            <span className="text-[11px] text-[#5B7282]">
              {language === 'ML' ? 'അപ്‌ഡേറ്റ് ചെയ്തത്:' : 'Updated:'} {lastRefreshed}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
          
          {/* Wave Height */}
          <div 
            onClick={() => navigate('/sea')}
            className="marine-card p-3.5 flex flex-col justify-between hover:border-[#176B87] transition-all cursor-pointer group"
          >
            <div className="flex items-center justify-between text-[#5B7282]">
              <span className="text-xs font-bold truncate">{t('waveHeight')}</span>
              <Waves className="w-4 h-4 text-[#176B87]" />
            </div>
            <div className="my-2">
              <span className="text-2xl sm:text-3xl font-black text-[#0B3954]">
                {data.waveHeight !== null ? `${data.waveHeight} m` : '—'}
              </span>
            </div>
            <span className="text-[11px] font-semibold text-[#16865B] truncate">
              {data.wavePeriod !== null ? `${data.wavePeriod}s ${language === 'ML' ? 'ഇടവേള' : 'period'}` : 'Normal Swell'}
            </span>
          </div>

          {/* Wind Speed */}
          <div 
            onClick={() => navigate('/weather')}
            className="marine-card p-3.5 flex flex-col justify-between hover:border-[#176B87] transition-all cursor-pointer group"
          >
            <div className="flex items-center justify-between text-[#5B7282]">
              <span className="text-xs font-bold truncate">{t('windSpeed')}</span>
              <Wind className="w-4 h-4 text-[#176B87]" />
            </div>
            <div className="my-2">
              <span className="text-2xl sm:text-3xl font-black text-[#0B3954]">
                {data.windSpeed !== null ? `${data.windSpeed}` : '—'}
              </span>
              <span className="text-xs font-bold text-[#5B7282] ml-1">km/h</span>
            </div>
            <span className="text-[11px] font-semibold text-[#176B87] truncate">
              {data.windDirection !== null ? `${data.windDirection}° ${language === 'ML' ? 'ദിശ' : 'heading'}` : 'Gentle Breeze'}
            </span>
          </div>

          {/* Air Temperature & Weather */}
          <div 
            onClick={() => navigate('/weather')}
            className="marine-card p-3.5 flex flex-col justify-between hover:border-[#176B87] transition-all cursor-pointer group"
          >
            <div className="flex items-center justify-between text-[#5B7282]">
              <span className="text-xs font-bold truncate">{t('temperature')}</span>
              <CloudSun className="w-4 h-4 text-[#D99116]" />
            </div>
            <div className="my-2">
              <span className="text-2xl sm:text-3xl font-black text-[#0B3954]">
                {data.airTemperature !== null ? `${data.airTemperature}°C` : '28°C'}
              </span>
            </div>
            <span className="text-[11px] font-semibold text-[#5B7282] truncate">
              {language === 'ML' ? data.weatherDescription.ml : data.weatherDescription.en}
            </span>
          </div>

          {/* Sea Temperature (SST) */}
          <div 
            onClick={() => navigate('/sea')}
            className="marine-card p-3.5 flex flex-col justify-between hover:border-[#176B87] transition-all cursor-pointer group"
          >
            <div className="flex items-center justify-between text-[#5B7282]">
              <span className="text-xs font-bold truncate">{t('seaTemperature')}</span>
              <Thermometer className="w-4 h-4 text-[#176B87]" />
            </div>
            <div className="my-2">
              <span className="text-2xl sm:text-3xl font-black text-[#0B3954]">
                {data.sst !== null ? `${data.sst}°C` : '28.5°C'}
              </span>
            </div>
            <span className="text-[11px] font-semibold text-[#16865B] truncate">
              {language === 'ML' ? 'അനുകൂല താപനില' : 'Optimal Boundary'}
            </span>
          </div>

        </div>
      </section>

      {/* 4. Quick Action Cards (Easy-To-Tap Navigation for Fishermen) */}
      <section className="space-y-2">
        <h3 className="text-sm font-extrabold text-[#0B3954] tracking-tight uppercase">
          {language === 'ML' ? 'പ്രധാന സേവനങ്ങൾ' : 'Quick Operations'}
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          
          {/* Card 1: Fishing Zones */}
          <div
            onClick={() => navigate('/zones')}
            className="marine-card p-4 flex items-center justify-between hover:border-[#176B87] hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-11 h-11 rounded-2xl bg-[#DFF3FA] flex items-center justify-center text-[#0B3954] flex-shrink-0 group-hover:scale-105 transition-transform">
                <Fish className="w-6 h-6 text-[#176B87]" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-[#0B3954] group-hover:text-[#176B87] transition-colors">
                  {language === 'ML' ? 'സാധ്യതയുള്ള മീൻപിടുത്ത മേഖലകൾ' : 'Potential Fishing Zones (PFZ)'}
                </span>
                <span className="text-xs text-[#5B7282]">
                  {language === 'ML' ? 'മത്സ്യ ലഭ്യത, ദൂരം, ഡീസൽ എസ്റ്റിമേറ്റ്' : 'Nearest hotspots, bearing & fuel saving'}
                </span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[#5B7282] group-hover:text-[#176B87] transition-colors" />
          </div>

          {/* Card 2: 24h Sea & Swell Forecast */}
          <div
            onClick={() => navigate('/sea')}
            className="marine-card p-4 flex items-center justify-between hover:border-[#176B87] hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-11 h-11 rounded-2xl bg-[#D9F3E6] flex items-center justify-center text-[#16865B] flex-shrink-0 group-hover:scale-105 transition-transform">
                <Waves className="w-6 h-6 text-[#16865B]" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-[#0B3954] group-hover:text-[#176B87] transition-colors">
                  {language === 'ML' ? '24 മണിക്കൂർ തിരമാല പ്രവചനം' : '24-Hour Sea & Swell Forecast'}
                </span>
                <span className="text-xs text-[#5B7282]">
                  {language === 'ML' ? 'വള്ളങ്ങൾക്കുള്ള സുരക്ഷാ നിർദ്ദേശങ്ങൾ' : 'Wave height, wave period & boat advice'}
                </span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[#5B7282] group-hover:text-[#176B87] transition-colors" />
          </div>

          {/* Card 3: Ask NeerMitra AI */}
          <div
            onClick={() => navigate('/assistant')}
            className="marine-card p-4 flex items-center justify-between hover:border-[#176B87] hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-11 h-11 rounded-2xl bg-[#DFF3FA] flex items-center justify-center text-[#0B3954] flex-shrink-0 group-hover:scale-105 transition-transform">
                <MessageSquare className="w-6 h-6 text-[#176B87]" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-[#0B3954] group-hover:text-[#176B87] transition-colors">
                  {language === 'ML' ? 'നീർമിത്ര എഐ സഹായി' : 'Ask NeerMitra AI Guide'}
                </span>
                <span className="text-xs text-[#5B7282]">
                  {language === 'ML' ? 'ശബ്ദത്തിലൂടെയോ ടൈപ്പ് ചെയ്തോ ചോദിക്കാം' : 'Voice queries in Malayalam & English'}
                </span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[#5B7282] group-hover:text-[#176B87] transition-colors" />
          </div>

          {/* Card 4: Emergency SOS */}
          <div
            onClick={() => navigate('/safety')}
            className="marine-card p-4 flex items-center justify-between border-[#F5B8B1] bg-[#FDF0EE]/50 hover:bg-[#FDF0EE] transition-all cursor-pointer group"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-11 h-11 rounded-2xl bg-[#FDF0EE] border border-[#F5B8B1] flex items-center justify-center text-[#C0392B] flex-shrink-0 group-hover:scale-105 transition-transform">
                <PhoneCall className="w-6 h-6 text-[#C0392B]" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-[#C0392B]">
                  {language === 'ML' ? 'അടിയന്തര സഹായം & SOS' : 'Emergency Help & SOS'}
                </span>
                <span className="text-xs text-[#5B7282]">
                  {language === 'ML' ? 'കോസ്റ്റ് ഗാർഡ് 1554 • എമർജൻസി 112' : 'Coast Guard 1554 • Police 1093 • SOS 112'}
                </span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[#C0392B]" />
          </div>

        </div>
      </section>

    </div>
  );
}
