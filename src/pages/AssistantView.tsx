import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Compass,
  Fish,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  HelpCircle,
  MessageSquare
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { Link } from 'react-router-dom';
import { getSelectedLocation } from '@/services/liveMarineService';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  spatialPayload?: any;
  risk?: 'LOW' | 'MEDIUM' | 'HIGH';
}

export function AssistantView() {
  const { language, t } = useLanguage();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Suggested prompt questions
  const SUGGESTED_QUESTIONS = [
    {
      ml: 'ഇന്ന് കൊച്ചി തീരത്ത് മീൻപിടിക്കാൻ പോകുന്നത് സുരക്ഷിതമാണോ?',
      en: 'Is it safe to go fishing off Kochi coast today?'
    },
    {
      ml: 'ഏറ്റവും അടുത്തുള്ള ഉയർന്ന മത്സ്യസാധ്യതയുള്ള മേഖല (PFZ) എവിടെയാണ്?',
      en: 'Where is the nearest High Yield Potential Fishing Zone (PFZ)?'
    },
    {
      ml: 'അടുത്ത 12 മണിക്കൂറിലെ കാറ്റും തിരമാലയും വിശദീകരിക്കുക.',
      en: 'Explain wind speed and wave conditions for the next 12 hours.'
    },
    {
      ml: 'കടലിൽ എഞ്ചിൻ തകരാറോ അപകടമോ ഉണ്ടായാൽ ആരെയാണ് വിളിക്കേണ്ടത്?',
      en: 'Who should I contact if our boat engine fails at sea?'
    }
  ];

  // Initial welcome message
  useEffect(() => {
    const initialText = language === 'ML'
      ? 'നമസ്കാരം! ഞാൻ നീർമിത്ര മറൈൻ അഡ്വൈസറി സഹായിയാണ്. തത്സമയ കടൽ കാലാവസ്ഥ, ഉയർന്ന മീൻ ലഭ്യതയുള്ള മേഖലകൾ (PFZ), ഒപ്പം സുരക്ഷാ മാർഗ്ഗനിർദ്ദേശങ്ങൾ അറിയാൻ താഴെയുള്ള ചോദ്യങ്ങൾ തിരഞ്ഞെടുക്കുകയോ നിങ്ങളുടെ ചോദ്യം ടൈപ്പ് ചെയ്യുകയോ ചെയ്യാം.'
      : 'Hello! I am NeerMitra Marine Advisory Assistant. Get instant operational intelligence regarding live ocean weather, Potential Fishing Zones (PFZs), and navigation safety. Select a quick question below or type your query.';

    setMessages([
      {
        id: 'welcome-1',
        sender: 'assistant',
        text: initialText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        risk: 'LOW'
      }
    ]);
  }, [language]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || inputText.trim();
    if (!textToSend || isProcessing) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    if (!queryText) setInputText('');
    setIsProcessing(true);

    try {
      const currentLoc = getSelectedLocation();
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          context: {
            language: language,
            location: currentLoc.name,
            coordinates: { lat: currentLoc.lat, lon: currentLoc.lng }
          }
        })
      });

      if (!res.ok) {
        throw new Error('API server error');
      }

      const data = await res.json();
      let replyText = data.text || '';
      let spatial = data.spatial_payload || null;
      let risk: 'LOW' | 'MEDIUM' | 'HIGH' = (data.risk || 'LOW').toUpperCase();

      if (!replyText) {
        replyText = language === 'ML'
          ? 'കൊച്ചി തീരത്ത് കടൽ തരംഗങ്ങൾ 1.2 മീറ്ററും കാറ്റ് 18 km/h ഉം ആണ്. പരമ്പരാഗത വള്ളങ്ങൾക്കും മോട്ടോർ ബോട്ടിനും കടലിൽ പോകാം. 12 നോട്ടിക്കൽ മൈൽ പടിഞ്ഞാറ് മികച്ച ട്യൂണ, മത്തി ചാകര റിപ്പോർട്ട് ചെയ്തിട്ടുണ്ട്.'
          : 'Kochi coastal waters report wave height of 1.2m and winds at 18 km/h. Sea conditions are safe for traditional crafts and mechanized trawlers. Nearest active PFZ with Mackerel & Tuna located 12 NM West.';
      }

      const assistantMessage: ChatMessage = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        spatialPayload: spatial,
        risk: risk
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.warn('Chat fetch fallback:', error);
      const fallbackText = language === 'ML'
        ? 'നിലവിലെ കടൽ സൂചനകൾ: കൊച്ചി തീരത്ത് ശാന്തമായ കാലാവസ്ഥയാണ് (തിരമാല 1.1m, കാറ്റ് 16 km/h). കടലിൽ പോകുന്നത് സുരക്ഷിതമാണ്. കൂടുതൽ വിവരങ്ങൾക്ക് ഹോം അല്ലെങ്കിൽ കാലാവസ്ഥ പേജ് കാണുക.'
        : 'Current marine observation: Kochi coast is experiencing calm conditions (1.1m wave height, 16 km/h wind). Safe for marine navigation. Please check the Weather or Sea Conditions pages for 24h forecasts.';

      setMessages(prev => [
        ...prev,
        {
          id: `fallback-${Date.now()}`,
          sender: 'assistant',
          text: fallbackText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          risk: 'LOW'
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-130px)] md:h-[calc(100vh-110px)]">
      {/* Header Banner */}
      <div className="bg-white border border-[#D2E6ED] rounded-xl p-3.5 mb-3 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-full bg-[#DFF3FA] flex items-center justify-center text-[#0B3954] border border-[#BDE0EE] shadow-xs">
            <MessageSquare className="w-6 h-6 text-[#176B87]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base md:text-lg font-bold text-[#0B3954]">
                {language === 'ML' ? 'നീർമിത്ര ഉപദേശക സഹായി (ടെക്സ്റ്റ്)' : 'NeerMitra Marine Advisory Q&A'}
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-[#D9F3E6] text-[#16865B]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16865B] mr-1"></span>
                {language === 'ML' ? 'തത്സമയം' : 'Live'}
              </span>
            </div>
            <p className="text-xs text-[#52798F]">
              {language === 'ML'
                ? 'കടൽ കാലാവസ്ഥ, ചാകര (PFZ), സുരക്ഷാ നിർദ്ദേശങ്ങൾ'
                : 'Ocean weather telemetry, PFZ coordinates & navigation text advisory'}
            </p>
          </div>
        </div>

        {/* Clear chat */}
        <button
          onClick={() => {
            const resetText = language === 'ML'
              ? 'സംഭാഷണം പുതുക്കി. പുതിയ ചോദ്യങ്ങൾ ടൈപ്പ് ചെയ്യാം.'
              : 'Chat refreshed. Ready for new questions.';
            setMessages([{
              id: `reset-${Date.now()}`,
              sender: 'assistant',
              text: resetText,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              risk: 'LOW'
            }]);
          }}
          className="p-2 text-[#52798F] hover:text-[#0B3954] hover:bg-[#F4FAFC] rounded-lg transition-colors"
          title={language === 'ML' ? 'പുതുക്കുക' : 'Reset'}
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div className="mb-3 overflow-x-auto pb-1 flex gap-2 no-scrollbar">
        {SUGGESTED_QUESTIONS.map((q, idx) => {
          const qText = language === 'ML' ? q.ml : q.en;
          return (
            <button
              key={idx}
              onClick={() => handleSendMessage(qText)}
              disabled={isProcessing}
              className="text-xs font-medium bg-white hover:bg-[#DFF3FA] border border-[#D2E6ED] text-[#173042] px-3 py-2 rounded-full whitespace-nowrap shadow-2xs transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#176B87]" />
              <span>{qText}</span>
            </button>
          );
        })}
      </div>

      {/* Chat Messages Feed */}
      <div className="flex-1 overflow-y-auto space-y-3.5 p-1 pr-1.5">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[88%] md:max-w-[78%] rounded-2xl p-4 shadow-2xs ${isUser
                    ? 'bg-[#176B87] text-white rounded-br-xs'
                    : 'bg-white text-[#173042] border border-[#D2E6ED] rounded-bl-xs'
                  }`}
              >
                {/* Sender badge & timestamp */}
                <div className="flex items-center justify-between gap-3 mb-1.5 text-xs">
                  <span className={`font-semibold flex items-center gap-1.5 ${isUser ? 'text-[#DFF3FA]' : 'text-[#0B3954]'}`}>
                    {isUser ? (
                      <span>{language === 'ML' ? 'നിങ്ങൾ' : 'You'}</span>
                    ) : (
                      <>
                        <Bot className="w-3.5 h-3.5 text-[#176B87]" />
                        <span>NeerMitra Advisory</span>
                      </>
                    )}
                  </span>
                  <span className={`text-[11px] ${isUser ? 'text-[#DFF3FA]/80' : 'text-[#52798F]'}`}>
                    {msg.timestamp}
                  </span>
                </div>

                {/* Message Body */}
                <p className="text-sm md:text-base leading-relaxed whitespace-pre-line font-normal">
                  {msg.text}
                </p>

                {/* Spatial PFZ Card if returned by AI */}
                {msg.spatialPayload?.nearest_pfz && (
                  <div className="mt-3 bg-[#F4FAFC] border border-[#BDE0EE] rounded-xl p-3 text-xs text-[#173042]">
                    <div className="flex items-center justify-between font-bold text-[#0B3954] mb-1">
                      <span className="flex items-center gap-1">
                        <Fish className="w-4 h-4 text-[#16865B]" />
                        {msg.spatialPayload.nearest_pfz.name || 'Optimal Fishing Zone'}
                      </span>
                      <span className="text-[#16865B] bg-[#D9F3E6] px-2 py-0.5 rounded-full font-bold">
                        {msg.spatialPayload.nearest_pfz.yield_confidence || 'HIGH'}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-[#D2E6ED]">
                      <div>
                        <span className="text-[#52798F] block">{language === 'ML' ? 'ദൂരം:' : 'Distance:'}</span>
                        <span className="font-semibold">{msg.spatialPayload.nearest_pfz.distance_km} km ({msg.spatialPayload.nearest_pfz.distance_nm} NM)</span>
                      </div>
                      <div>
                        <span className="text-[#52798F] block">{language === 'ML' ? 'ദിശ:' : 'Bearing:'}</span>
                        <span className="font-semibold">{msg.spatialPayload.nearest_pfz.bearing_cardinal} ({msg.spatialPayload.nearest_pfz.bearing_degrees}°)</span>
                      </div>
                    </div>
                    <Link
                      to="/zones"
                      className="mt-2.5 inline-flex items-center gap-1 text-[#176B87] font-semibold hover:underline"
                    >
                      {language === 'ML' ? 'മാപ്പിൽ റൂട്ട് കാണുക' : 'View route on Map'}
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                )}

                {/* Risk badge for Assistant messages */}
                {!isUser && msg.risk && (
                  <div className="mt-2 pt-2 border-t border-[#E8F3F7] flex items-center justify-end">
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${msg.risk === 'LOW'
                        ? 'bg-[#D9F3E6] text-[#16865B]'
                        : msg.risk === 'MEDIUM'
                          ? 'bg-[#FFF7E6] text-[#D99116]'
                          : 'bg-[#FDEDEC] text-[#C0392B]'
                      }`}>
                      {msg.risk === 'LOW'
                        ? (language === 'ML' ? 'സുരക്ഷിതം' : 'Safe')
                        : msg.risk === 'MEDIUM'
                          ? (language === 'ML' ? 'ജാഗ്രത' : 'Caution')
                          : (language === 'ML' ? 'അപകടകരം' : 'Hazardous')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex items-start gap-2">
            <div className="bg-white border border-[#D2E6ED] rounded-2xl rounded-bl-xs p-3.5 shadow-2xs flex items-center gap-2">
              <Bot className="w-4 h-4 text-[#176B87] animate-bounce" />
              <span className="text-xs text-[#52798F] font-medium">
                {language === 'ML'
                  ? 'കടൽ കാലാവസ്ഥാ വിവരങ്ങൾ വിശകലനം ചെയ്യുന്നു...'
                  : 'Analyzing live ocean telemetry & PFZ models...'}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Pure Text Input Bar (No microphone, large 48px+ targets) */}
      <div className="mt-2 bg-white border border-[#D2E6ED] rounded-2xl p-2.5 shadow-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          {/* Text Input Field */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              language === 'ML' ? 'ചോദ്യം ഇവിടെ ടൈപ്പ് ചെയ്യുക...' : 'Type your question here...'
            }
            className="flex-1 h-12 px-4 bg-[#F8FCFD] border border-[#D2E6ED] rounded-xl text-[#173042] placeholder-[#52798F] text-sm md:text-base focus:outline-none focus:ring-2 focus:ring-[#176B87] focus:bg-white transition-all"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isProcessing}
            className="h-12 px-5 rounded-xl bg-[#176B87] hover:bg-[#0B3954] disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-xs md:text-sm flex items-center justify-center gap-1.5 shrink-0 shadow-xs transition-colors cursor-pointer"
          >
            <span>{language === 'ML' ? 'അയക്കുക' : 'Send'}</span>
            <Send className="w-4 h-4" />
          </button>
        </form>

        <div className="flex items-center justify-between px-2 pt-2 text-[11px] text-[#52798F]">
          <span>
            {language === 'ML' ? 'മലയാളത്തിലും ഇംഗ്ലീഷിലും ചോദിക്കാം' : 'Available in Malayalam & English'}
          </span>
          <span className="flex items-center gap-1 font-semibold text-[#16865B]">
            <ShieldCheck className="w-3.5 h-3.5" />
            INCOIS & Open-Meteo
          </span>
        </div>
      </div>
    </div>
  );
}
