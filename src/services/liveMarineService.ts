/**
 * Live Marine Telemetry Service for NeerMitra
 * Integrates real-time oceanographic & meteorological data from Open-Meteo Marine APIs
 * Covering Indian EEZ & Arabian Sea sectors (Kochi, Goa, Mumbai, Chennai, etc.)
 */

export interface HourlyForecastItem {
  time: string;
  hour: string;
  temp: number;
  waveHeight: number;
  windSpeed: number;
  rainProb: number;
}

export interface LiveMarineData {
  locationName: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  sst: number | null; // Sea Surface Temp °C
  sstAnomaly: number | null;
  waveHeight: number | null; // Significant wave height in meters
  swellHeight: number | null; // Swell height in meters
  wavePeriod: number | null; // Wave period in seconds
  waveDirection: number | null; // Wave direction in degrees
  windSpeed: number | null; // Wind speed in km/h
  windDirection: number | null; // Wind direction in degrees
  windGusts: number | null; // Wind gusts in km/h
  airTemperature: number | null; // Air temp °C
  relativeHumidity: number | null; // %
  visibilityKm: number | null; // km
  weatherCode: number | null; // WMO Code
  weatherDescription: { en: string; ml: string };
  riskScore: number | null; // 0-100 calculated safety index
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  statusSummary: string;
  statusSummaryMl: string;
  hourlyForecast: HourlyForecastItem[];
  isLive: boolean;
}

export interface CoastalSector {
  id: string;
  name: string;
  nameMl: string;
  region: string;
  lat: number;
  lng: number;
}

export const COASTAL_SECTORS: CoastalSector[] = [
  { id: 'kochi', name: 'Kochi Sector K-04', nameMl: 'കൊച്ചി സെക്ടർ K-04', region: 'Kerala · Arabian Sea', lat: 9.9312, lng: 75.8234 },
  { id: 'munambam', name: 'Munambam Sector M-02', nameMl: 'മുനമ്പം സെക്ടർ M-02', region: 'Kerala · Arabian Sea', lat: 10.20, lng: 75.80 },
  { id: 'alappuzha', name: 'Alappuzha Shoals A-09', nameMl: 'ആലപ്പുഴ ഷോളുകൾ A-09', region: 'Kerala · Arabian Sea', lat: 9.45, lng: 76.15 },
  { id: 'goa', name: 'Goa Coastal Zone G-08', nameMl: 'ഗോവ കോസ്റ്റൽ സോൺ G-08', region: 'Goa · Arabian Sea', lat: 15.35, lng: 73.55 },
  { id: 'mumbai', name: 'Mumbai High Corridor B-12', nameMl: 'മുംബൈ ഹൈ കോറിഡോർ B-12', region: 'Maharashtra · Arabian Sea', lat: 18.90, lng: 72.40 },
  { id: 'mangalore', name: 'Mangalore Deep MN-03', nameMl: 'മംഗളൂരു ഡീപ് MN-03', region: 'Karnataka · Arabian Sea', lat: 12.82, lng: 74.52 },
  { id: 'kutch', name: 'Gulf of Kutch GK-05', nameMl: 'ഗൾഫ് ഓഫ് കച്ച് GK-05', region: 'Gujarat · Arabian Sea', lat: 22.40, lng: 69.20 },
  { id: 'chennai', name: 'Chennai Coromandel C-03', nameMl: 'ചെന്നൈ കോറമാണ്ടൽ C-03', region: 'Tamil Nadu · Bay of Bengal', lat: 13.10, lng: 80.45 },
  { id: 'rameswaram', name: 'Palk Strait / Rameswaram R-01', nameMl: 'പാക്ക് കടലിടുക്ക് / രാമേശ്വരം R-01', region: 'Tamil Nadu · Palk Strait', lat: 9.25, lng: 79.35 },
  { id: 'vizag', name: 'Visakhapatnam Shelf V-06', nameMl: 'വിശാഖപട്ടണം ഷെൽഫ് V-06', region: 'Andhra Pradesh · Bay of Bengal', lat: 17.65, lng: 83.42 },
  { id: 'paradip', name: 'Paradip Coastal Sector P-02', nameMl: 'പാരദ്വീപ് കോസ്റ്റൽ സെക്ടർ P-02', region: 'Odisha · Bay of Bengal', lat: 20.20, lng: 86.68 },
  { id: 'sundarbans', name: 'Sundarbans Marine Sector SB-01', nameMl: 'സുന്ദർബൻസ് മറൈൻ SB-01', region: 'West Bengal · Bay of Bengal', lat: 21.50, lng: 88.50 },
];

function calculateDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export function getNearestCoastalSector(lat: number, lng: number): { sector: CoastalSector; distanceKm: number } {
  let nearest = COASTAL_SECTORS[0];
  let minDistance = Infinity;

  for (const sector of COASTAL_SECTORS) {
    const dist = calculateDistanceKm(lat, lng, sector.lat, sector.lng);
    if (dist < minDistance) {
      minDistance = dist;
      nearest = sector;
    }
  }

  return { sector: nearest, distanceKm: Math.round(minDistance) };
}

export function getWeatherConditionText(code: number | null): { en: string; ml: string } {
  if (code === null) return { en: 'Fair Sea State', ml: 'സാധാരണ കടൽാവസ്ഥ' };
  if (code === 0) return { en: 'Clear Sky', ml: 'തെളിഞ്ഞ ആകാശം' };
  if (code <= 3) return { en: 'Partly Cloudy', ml: 'ഭാഗികമായി മേഘാവൃതം' };
  if (code >= 45 && code <= 48) return { en: 'Foggy / Reduced Visibility', ml: 'മൂടൽമഞ്ഞ്' };
  if (code >= 51 && code <= 55) return { en: 'Light Drizzle', ml: 'ചാറ്റൽ മഴ' };
  if (code >= 61 && code <= 65) return { en: 'Moderate Rain', ml: 'മിതമായ മഴ' };
  if (code >= 80 && code <= 82) return { en: 'Passing Showers', ml: 'ഇടയ്ക്കിടെയുള്ള മഴ' };
  if (code >= 95) return { en: 'Thunderstorm Warning', ml: 'ഇടിമിന്നൽ മുന്നറിയിപ്പ്' };
  return { en: 'Cloudy Conditions', ml: 'മേഘാവൃതമായ അന്തരീക്ഷം' };
}

export interface SelectedLocation {
  lat: number;
  lng: number;
  name: string;
  nameMl?: string;
  isGps?: boolean;
}

const STORAGE_KEY = 'neermitra_selected_location';

export function getSelectedLocation(): SelectedLocation {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (typeof parsed.lat === 'number' && typeof parsed.lng === 'number' && parsed.name) {
        return parsed;
      }
    }
  } catch {}
  return {
    lat: COASTAL_SECTORS[0].lat,
    lng: COASTAL_SECTORS[0].lng,
    name: COASTAL_SECTORS[0].name,
    nameMl: COASTAL_SECTORS[0].nameMl
  };
}

export function setSelectedLocation(loc: SelectedLocation) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(loc));
  } catch {}
}

const unavailableMarineData: LiveMarineData = {
  locationName: 'Kochi Sector K-04',
  latitude: 9.9312,
  longitude: 75.8234,
  timestamp: new Date().toISOString(),
  sst: null,
  sstAnomaly: null,
  waveHeight: null,
  swellHeight: null,
  wavePeriod: null,
  waveDirection: null,
  windSpeed: null,
  windDirection: null,
  windGusts: null,
  airTemperature: null,
  relativeHumidity: null,
  visibilityKm: null,
  weatherCode: null,
  weatherDescription: { en: 'Waiting for telemetry', ml: 'വിവരങ്ങൾ ലഭ്യമാക്കുന്നു' },
  riskScore: null,
  riskLevel: 'LOW',
  statusSummary: 'Waiting for live marine telemetry',
  statusSummaryMl: 'കടൽ വിവരങ്ങൾ ലഭിക്കാൻ കാത്തിരിക്കുന്നു',
  hourlyForecast: [],
  isLive: false
};

let cachedMarineData: LiveMarineData = { ...unavailableMarineData };
let lastFetchTime = 0;
const CACHE_TTL_MS = 60 * 1000; // 1 minute cache

export async function fetchLiveMarineData(
  lat?: number, 
  lng?: number,
  customLocationName?: string,
  forceRefresh: boolean = false
): Promise<LiveMarineData> {
  const currentLoc = getSelectedLocation();
  const targetLat = typeof lat === 'number' ? lat : currentLoc.lat;
  const targetLng = typeof lng === 'number' ? lng : currentLoc.lng;
  const targetLocationName = customLocationName || (
    Math.abs(targetLat - currentLoc.lat) < 0.001 && Math.abs(targetLng - currentLoc.lng) < 0.001
      ? currentLoc.name
      : undefined
  );

  const now = Date.now();
  const isSameLocation = 
    Math.abs(cachedMarineData.latitude - targetLat) < 0.001 && 
    Math.abs(cachedMarineData.longitude - targetLng) < 0.001;

  if (!forceRefresh && isSameLocation && now - lastFetchTime < CACHE_TTL_MS && cachedMarineData.isLive) {
    return cachedMarineData;
  }

  try {
    // 1. Fetch Real-time Marine Data (waves, swell)
    const marineUrl = `https://marine-api.open-meteo.com/v1/marine?latitude=${targetLat}&longitude=${targetLng}&current=wave_height,wave_direction,wave_period,swell_wave_height,sea_surface_temperature&hourly=wave_height,wave_period&forecast_days=2`;
    
    // 2. Fetch Real-time Weather Data (wind, temperature, rain, visibility)
    const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${targetLat}&longitude=${targetLng}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility&hourly=temperature_2m,precipitation_probability,wind_speed_10m&forecast_days=2`;

    const [marineRes, weatherRes] = await Promise.allSettled([
      fetch(marineUrl).then(r => {
        if (!r.ok) throw new Error(`Marine API responded ${r.status}`);
        return r.json();
      }),
      fetch(weatherUrl).then(r => {
        if (!r.ok) throw new Error(`Weather API responded ${r.status}`);
        return r.json();
      })
    ]);

    let waveHeight: number | null = null;
    let swellHeight: number | null = null;
    let wavePeriod: number | null = null;
    let waveDirection: number | null = null;
    let sst: number | null = null;
    let windSpeed: number | null = null;
    let windDirection: number | null = null;
    let windGusts: number | null = null;
    let airTemperature: number | null = null;
    let relativeHumidity: number | null = null;
    let visibilityKm: number | null = null;
    let weatherCode: number | null = null;

    let hourlyForecast: HourlyForecastItem[] = [];

    if (marineRes.status === 'fulfilled' && marineRes.value?.current) {
      const m = marineRes.value.current;
      if (typeof m.wave_height === 'number') waveHeight = Number(m.wave_height.toFixed(1));
      if (typeof m.swell_wave_height === 'number') swellHeight = Number(m.swell_wave_height.toFixed(1));
      if (typeof m.wave_period === 'number') wavePeriod = Number(m.wave_period.toFixed(1));
      if (typeof m.wave_direction === 'number') waveDirection = Math.round(m.wave_direction);
      if (typeof m.sea_surface_temperature === 'number') sst = Number(m.sea_surface_temperature.toFixed(1));
    }

    if (weatherRes.status === 'fulfilled' && weatherRes.value?.current) {
      const w = weatherRes.value.current;
      if (typeof w.temperature_2m === 'number') airTemperature = Math.round(w.temperature_2m);
      if (typeof w.relative_humidity_2m === 'number') relativeHumidity = Math.round(w.relative_humidity_2m);
      if (typeof w.wind_speed_10m === 'number') windSpeed = Number(w.wind_speed_10m.toFixed(1));
      if (typeof w.wind_direction_10m === 'number') windDirection = Math.round(w.wind_direction_10m);
      if (typeof w.wind_gusts_10m === 'number') windGusts = Number(w.wind_gusts_10m.toFixed(1));
      if (typeof w.visibility === 'number') visibilityKm = Math.round(w.visibility / 1000);
      if (typeof w.weather_code === 'number') weatherCode = w.weather_code;

      // Extract 6-hour forecast intervals for simple fisherman cards
      if (weatherRes.value?.hourly?.time) {
        const hTimes = weatherRes.value.hourly.time.slice(0, 12);
        const hTemps = weatherRes.value.hourly.temperature_2m || [];
        const hRains = weatherRes.value.hourly.precipitation_probability || [];
        const hWinds = weatherRes.value.hourly.wind_speed_10m || [];
        const hWaves = marineRes.status === 'fulfilled' && marineRes.value?.hourly?.wave_height ? marineRes.value.hourly.wave_height : [];

        hourlyForecast = hTimes.map((t: string, idx: number) => {
          const date = new Date(t);
          const hour = date.getHours();
          const hourLabel = `${hour % 12 || 12} ${hour >= 12 ? 'PM' : 'AM'}`;
          return {
            time: t,
            hour: hourLabel,
            temp: Math.round(hTemps[idx] ?? airTemperature ?? 28),
            rainProb: Math.round(hRains[idx] ?? 0),
            waveHeight: Number((hWaves[idx] ?? waveHeight ?? 1.2).toFixed(1)),
            windSpeed: Math.round(hWinds[idx] ?? windSpeed ?? 14),
          };
        });
      }
    }

    // Determine location name
    let resolvedLocationName = targetLocationName;
    if (!resolvedLocationName) {
      const { sector, distanceKm } = getNearestCoastalSector(targetLat, targetLng);
      resolvedLocationName = distanceKm < 30 ? sector.name : `${sector.name} (~${distanceKm}km)`;
    }

    setSelectedLocation({
      lat: targetLat,
      lng: targetLng,
      name: resolvedLocationName
    });

    // Inland fallback for marine readings
    if (waveHeight === null && sst === null) {
      const { sector } = getNearestCoastalSector(targetLat, targetLng);
      try {
        const fallbackUrl = `https://marine-api.open-meteo.com/v1/marine?latitude=${sector.lat}&longitude=${sector.lng}&current=wave_height,wave_direction,wave_period,swell_wave_height,sea_surface_temperature`;
        const fbRes = await fetch(fallbackUrl);
        if (fbRes.ok) {
          const fbData = await fbRes.json();
          if (fbData?.current) {
            const fm = fbData.current;
            if (typeof fm.wave_height === 'number') waveHeight = Number(fm.wave_height.toFixed(1));
            if (typeof fm.swell_wave_height === 'number') swellHeight = Number(fm.swell_wave_height.toFixed(1));
            if (typeof fm.wave_period === 'number') wavePeriod = Number(fm.wave_period.toFixed(1));
            if (typeof fm.wave_direction === 'number') waveDirection = Math.round(fm.wave_direction);
            if (typeof fm.sea_surface_temperature === 'number') sst = Number(fm.sea_surface_temperature.toFixed(1));
          }
        }
      } catch {
        // Continue
      }
    }

    if (waveHeight === null && windSpeed === null && sst === null) {
      throw new Error('Live providers returned no marine observations');
    }

    // Calculate real-time dynamic Maritime Risk Index (0 - 100)
    let riskScore = 15;
    riskScore += waveHeight === null ? 0 : Math.min(45, (waveHeight / 3.0) * 45);
    riskScore += windSpeed === null ? 0 : Math.min(30, (windSpeed / 50.0) * 30);
    riskScore += windGusts === null ? 0 : Math.min(15, (windGusts / 60.0) * 15);
    riskScore = Math.round(Math.min(100, Math.max(5, riskScore)));

    let riskLevel: LiveMarineData['riskLevel'] = 'LOW';
    let statusSummary = 'Sea is calm and safe for coastal fishing crafts.';
    let statusSummaryMl = 'കടൽ ശാന്തമാണ്. ചെറിയ വള്ളങ്ങൾക്കും ബോട്ടുകൾക്കും പോകാൻ അനുയോജ്യം.';

    if (riskScore >= 75 || (waveHeight !== null && waveHeight >= 3.0) || (windSpeed !== null && windSpeed >= 50)) {
      riskLevel = 'CRITICAL';
      statusSummary = 'GALE / ROUGH SEAS — Coastal craft advisory in effect. Do NOT venture out.';
      statusSummaryMl = 'കടൽ പ്രക്ഷുബ്ധമാണ്. അതിശക്തമായ കാറ്റും തിരമാലകളും. ആരും കടലിൽ പോകരുത്.';
    } else if (riskScore >= 50 || (waveHeight !== null && waveHeight >= 2.2) || (windSpeed !== null && windSpeed >= 35)) {
      riskLevel = 'HIGH';
      statusSummary = 'Elevated monsoonal swell — Exercise caution past 15 NM.';
      statusSummaryMl = 'ഉയർന്ന തിരമാലകൾ. ആഴക്കടൽ മേഖലകളിലേക്ക് പോകുന്നത് ഒഴിവാക്കുക.';
    } else if (riskScore >= 30 || (waveHeight !== null && waveHeight >= 1.7)) {
      riskLevel = 'MEDIUM';
      statusSummary = 'Moderate chop — Standard navigation protocols apply.';
      statusSummaryMl = 'മിതമായ തിരമാലകൾ. സാധാരണ സുരക്ഷാ മുൻകരുതലുകൾ പാലിക്കുക.';
    }

    cachedMarineData = {
      locationName: resolvedLocationName,
      latitude: targetLat,
      longitude: targetLng,
      timestamp: new Date().toISOString(),
      sst,
      sstAnomaly: null,
      waveHeight,
      swellHeight,
      wavePeriod,
      waveDirection,
      windSpeed,
      windDirection,
      windGusts,
      airTemperature: airTemperature ?? 29,
      relativeHumidity: relativeHumidity ?? 78,
      visibilityKm: visibilityKm ?? 15,
      weatherCode,
      weatherDescription: getWeatherConditionText(weatherCode),
      riskScore,
      riskLevel,
      statusSummary,
      statusSummaryMl,
      hourlyForecast,
      isLive: true
    };

    lastFetchTime = now;
    return cachedMarineData;
  } catch (err) {
    console.warn('Using cached/fallback marine data due to network error:', err);
    return cachedMarineData;
  }
}

export function getCachedMarineData(): LiveMarineData {
  const currentLoc = getSelectedLocation();
  if (!cachedMarineData.isLive) {
    cachedMarineData.locationName = currentLoc.name;
    cachedMarineData.latitude = currentLoc.lat;
    cachedMarineData.longitude = currentLoc.lng;
  }
  return cachedMarineData;
}
