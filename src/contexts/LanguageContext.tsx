import React, { createContext, useContext, useState } from 'react';

export type SupportedLanguage = 'ML' | 'EN' | 'TA' | 'TE' | 'HI' | 'KN' | 'BN';

export interface LanguageInfo {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
}

export const LANGUAGES: LanguageInfo[] = [
  { code: 'ML', name: 'Malayalam', nativeName: 'മലയാളം' },
  { code: 'EN', name: 'English', nativeName: 'English' },
  { code: 'TA', name: 'Tamil', nativeName: 'தமிழ்' },
  { code: 'TE', name: 'Telugu', nativeName: 'తెలుగు' },
  { code: 'HI', name: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'KN', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
  { code: 'BN', name: 'Bengali', nativeName: 'বাংলা' },
];

const TRANSLATIONS: Record<string, Record<SupportedLanguage, string>> = {
  appName: {
    ML: 'നീർമിത്ര',
    EN: 'NeerMitra',
    TA: 'நீர்மিত্রா',
    TE: 'నీర్మిత్రా',
    HI: 'नीरमित्र',
    KN: 'ನೀರ್ಮಿತ್ರ',
    BN: 'নীরমিত্র'
  },
  appTagline: {
    ML: 'മത്സ്യത്തൊഴിലാളി സഹായി',
    EN: 'Marine Assistant for Fishermen',
    TA: 'மீனவர் கடல் வழிகாட்டி',
    TE: 'మత్స్యకారుల సముద్ర మార్గదర్శి',
    HI: 'मछुआरों का समुद्री साथी',
    KN: 'ಮೀನುಗಾರರ ಕಡಲ ಸಹಾಯಕ',
    BN: 'জেলেদের সামুদ্রিক গাইড'
  },
  navHome: {
    ML: 'ഹോം',
    EN: 'Home',
    TA: 'முகப்பு',
    TE: 'హోమ్',
    HI: 'होम',
    KN: 'ಮುಖಪುಟ',
    BN: 'হোম'
  },
  navWeather: {
    ML: 'കാലാവസ്ഥ',
    EN: 'Weather',
    TA: 'வானிலை',
    TE: 'వాతావరణం',
    HI: 'मौसम',
    KN: 'ಹವಾಮಾನ',
    BN: 'আবহাওয়া'
  },
  navSea: {
    ML: 'കടൽ നില',
    EN: 'Sea State',
    TA: 'கடல் நிலை',
    TE: 'సముద్ర స్థితి',
    HI: 'समुद्र स्थिति',
    KN: 'ಕಡಲ ಸ್ಥಿತಿ',
    BN: 'সমুদ্র অবস্থা'
  },
  navZones: {
    ML: 'മീൻപിടുത്തം',
    EN: 'Fish Zones',
    TA: 'மீன்பிடி மண்டலம்',
    TE: 'చేపల వేట ప్రాంతాలు',
    HI: 'मत्स्य क्षेत्र',
    KN: 'ಮೀನುಗಾರಿಕೆ ವಲಯ',
    BN: 'মাছ ধরা অঞ্চল'
  },
  navAssistant: {
    ML: 'സഹായി (ടെക്സ്റ്റ്)',
    EN: 'Advisory Q&A',
    TA: 'உதவியாளர்',
    TE: 'సహాయకుడు',
    HI: 'सहायक',
    KN: 'ಸಹಾಯಕ',
    BN: 'সহায়ক'
  },
  navSafety: {
    ML: 'സുരക്ഷ & SOS',
    EN: 'Safety & SOS',
    TA: 'பாதுகாப்பு & SOS',
    TE: 'రక్షణ & SOS',
    HI: 'सुरक्षा & SOS',
    KN: 'ಸುರಕ್ಷತೆ & SOS',
    BN: 'নিরাপত্তা ও এসওএস'
  },
  todayVerdict: {
    ML: 'ഇന്ന് കടലിൽ പോകുന്നത് സുരക്ഷിതമാണോ?',
    EN: 'Is it safe to go fishing today?',
    TA: 'இன்று கடலுக்கு செல்வது பாதுகாப்பானதா?',
    TE: 'ఈ రోజు సముద్రంలోకి వెళ్లడం సురక్షితమేనా?',
    HI: 'क्या आज समुद्र में जाना सुरक्षित है?',
    KN: 'ಇಂದು ಸಮುದ್ರಕ್ಕೆ ಹೋಗುವುದು ಸುರಕ್ಷಿತವೇ?',
    BN: 'আজ কি সমুদ্রে যাওয়া নিরাপদ?'
  },
  safeCondition: {
    ML: 'കടൽ ശാന്തമാണ് - പോകാൻ സുരക്ഷിതം',
    EN: 'Safe for fishing today',
    TA: 'கடல் அமைதியாக உள்ளது - செல்வது பாதுகாப்பானது',
    TE: 'సముద్రం ప్రశాంతంగా ఉంది - సురక్షితం',
    HI: 'समुद्र शांत है - जाने के लिए सुरक्षित',
    KN: 'ಸಮುದ್ರ ಶಾಂತವಾಗಿದೆ - ಹೋಗಲು ಸುರಕ್ಷಿತ',
    BN: 'সমুদ্র শান্ত - মাছ ধরার জন্য নিরাপদ'
  },
  cautionCondition: {
    ML: 'ജാഗ്രത പാലിക്കുക - മിതമായ തിരമാലകൾ',
    EN: 'Caution advised - Moderate waves',
    TA: 'எச்சரிக்கையுடன் செல்லவும் - மிதமான அலைகள்',
    TE: 'జాగ్రత్త అవసరం - మోస్తరు అలలు',
    HI: 'सावधानी बरतें - मध्यम लहरें',
    KN: 'ಎಚ್ಚರಿಕೆ ವಹಿಸಿ - ಮಧ್ಯಮ ಅಲೆಗಳು',
    BN: 'সতর্কতা প্রয়োজন - মাঝারি ঢেউ'
  },
  dangerCondition: {
    ML: 'അപകടകരം - കടലിൽ പോകരുത്!',
    EN: 'Hazardous - Do NOT go out to sea!',
    TA: 'ஆபத்தானது - கடலுக்கு செல்ல வேண்டாம்!',
    TE: 'ప్రమాదకరం - సముద్రంలోకి వెళ్లవద్దు!',
    HI: 'खतरनाक - समुद्र में न जाएं!',
    KN: 'ಅಪಾಯಕಾರಿ - ಸಮುದ್ರಕ್ಕೆ ಹೋಗಬೇಡಿ!',
    BN: 'বিপজ্জনক - সমুদ্রে যাবেন না!'
  },
  waveHeight: {
    ML: 'തിരമാലയുടെ ഉയരം',
    EN: 'Wave Height',
    TA: 'அலை உயரம்',
    TE: 'అలల ఎత్తు',
    HI: 'लहरों की ऊंचाई',
    KN: 'ಅಲೆಗಳ ಎತ್ತರ',
    BN: 'ঢেউয়ের উচ্চতা'
  },
  windSpeed: {
    ML: 'കാറ്റിന്റെ വേഗത',
    EN: 'Wind Speed',
    TA: 'காற்றின் வேகம்',
    TE: 'గాలి వేగం',
    HI: 'हवा की गति',
    KN: 'ಗಾಳಿಯ ವೇಗ',
    BN: 'বাতাসের গতি'
  },
  temperature: {
    ML: 'വായു താപനില',
    EN: 'Air Temperature',
    TA: 'வெப்பநிலை',
    TE: 'ఉష్ణోగ్రత',
    HI: 'तापमान',
    KN: 'ತಾಪಮಾನ',
    BN: 'বায়ুর তাপমাত্রা'
  },
  seaTemperature: {
    ML: 'കടൽ താപനില (SST)',
    EN: 'Sea Temperature (SST)',
    TA: 'கடல் நீர் வெப்பநிலை',
    TE: 'సముద్ర ఉపరితల ఉష్ణోగ్రత',
    HI: 'समुद्री तापमान',
    KN: 'ಕಡಲ ತಾಪಮಾನ',
    BN: 'সমুদ্রের তাপমাত্রা'
  },
  rainChance: {
    ML: 'മഴ സാധ്യത',
    EN: 'Rain Probability',
    TA: 'மழை வாய்ப்பு',
    TE: 'వర్షం పడే అవకాశం',
    HI: 'बारिश की संभावना',
    KN: 'ಮಳೆ ಸಂಭವನೀಯತೆ',
    BN: 'বৃষ্টির সম্ভাবনা'
  },
  fishingYield: {
    ML: 'മീൻ ലഭ്യത സാധ്യത',
    EN: 'Fishing Suitability',
    TA: 'மீன் கிடைக்கும் வாய்ப்பு',
    TE: 'చేపల లభ్యత అవకాశం',
    HI: 'मछली मिलने की संभावना',
    KN: 'ಮೀನು ಇಳುವರಿ ನಿರೀಕ್ಷೆ',
    BN: 'মাছ পাওয়ার সম্ভাবনা'
  },
  selectLocation: {
    ML: 'തീരദേശ മേഖല തിരഞ്ഞെടുക്കുക',
    EN: 'Select Coastal Sector',
    TA: 'கடற்கரை மண்டலத்தை தேர்ந்தெடுக்கவும்',
    TE: 'తీరప్రాంతాన్ని ఎంచుకోండి',
    HI: 'तटीय क्षेत्र चुनें',
    KN: 'ಕರಾವಳಿ ವಲಯ ಆಯ್ಕೆಮಾಡಿ',
    BN: 'উপকূলীয় অঞ্চল নির্বাচন করুন'
  },
  useGps: {
    ML: 'എന്റെ സ്ഥാനം കണ്ടെത്തുക (GPS)',
    EN: 'Use My GPS Location',
    TA: 'என் இருப்பிடத்தை கண்டறி (GPS)',
    TE: 'నా స్థానాన్ని గుర్తించు (GPS)',
    HI: 'मेरा स्थान ढूंढें (GPS)',
    KN: 'ನನ್ನ ಸ್ಥಳ ಪತ್ತೆ ಮಾಡಿ (GPS)',
    BN: 'আমার অবস্থান সনাক্ত করুন (GPS)'
  },
  sosButton: {
    ML: 'അടിയന്തര SOS 112',
    EN: 'Emergency SOS 112',
    TA: 'அவசர SOS 112',
    TE: 'అత్యవసర SOS 112',
    HI: 'आपातकालीन SOS 112',
    KN: 'ತುರ್ತು SOS 112',
    BN: 'জরুরি এসওএস ১১২'
  },
  coastGuardCall: {
    ML: 'കോസ്റ്റ് ഗാർഡ് 1554',
    EN: 'Coast Guard 1554',
    TA: 'கடலோர காவல்படை 1554',
    TE: 'కోస్ట్ గార్డ్ 1554',
    HI: 'तटरक्षक बल 1554',
    KN: 'ಕೋಸ್ಟ್ ಗಾರ್ಡ್ 1554',
    BN: 'কোস্ট গার্ড ১৫৫৪'
  },
  askQuestion: {
    ML: 'ചോദ്യം ഇവിടെ ടൈപ്പ് ചെയ്യുക...',
    EN: 'Type your question here...',
    TA: 'கேள்வியை இங்கே உள்ளிடவும்...',
    TE: 'ప్రశ్నను ఇక్కడ టైప్ చేయండి...',
    HI: 'अपना सवाल यहाँ टाइप करें...',
    KN: 'ಪ್ರಶ್ನೆ ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ...',
    BN: 'প্রশ্ন এখানে টাইপ করুন...'
  }
};

interface LanguageContextType {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    const saved = localStorage.getItem('neermitra_lang') as SupportedLanguage;
    return saved && LANGUAGES.some(l => l.code === saved) ? saved : 'EN';
  });

  const setLanguage = (lang: SupportedLanguage) => {
    setLanguageState(lang);
    localStorage.setItem('neermitra_lang', lang);
  };

  const t = (key: string): string => {
    if (TRANSLATIONS[key] && TRANSLATIONS[key][language]) {
      return TRANSLATIONS[key][language];
    }
    if (TRANSLATIONS[key] && TRANSLATIONS[key]['EN']) {
      return TRANSLATIONS[key]['EN'];
    }
    return key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
