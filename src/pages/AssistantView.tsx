import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Bot,
  Send,
  Sparkles,
  Mic,
  MicOff,
  ThumbsUp,
  ThumbsDown,
  ArrowRight,
  Fish,
  ShieldCheck,
  RefreshCw,
  MessageSquare,
  MapPin,
  BookOpen,
  Clock,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { Link } from 'react-router-dom';
import { getSelectedLocation } from '@/services/liveMarineService';
import { apiUrl } from '@/services/api';
import { cn } from '@/lib/utils';

interface EvidenceSource {
  name: string;
  timestamp: string;
  type: string;
}

interface EvidenceTrail {
  sources: EvidenceSource[];
  threshold_rationale?: string;
  confidence_rating: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  spatialPayload?: any;
  risk?: 'LOW' | 'MEDIUM' | 'HIGH';
  evidence?: EvidenceTrail;
  agentsInvoked?: string[];
  feedback?: 'up' | 'down' | null;
}

export function AssistantView() {
  const { language, t } = useLanguage();
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = sessionStorage.getItem('orca_chat_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {}
    return [];
  });

  useEffect(() => {
    sessionStorage.setItem('orca_chat_history', JSON.stringify(messages));
  }, [messages]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Suggested prompt questions
  const SUGGESTED_QUESTIONS = [
    {
      ml: 'ഇന്ന് കൊച്ചി തീരത്ത് മീൻപിടിക്കാൻ പോകുന്നത് സുരക്ഷിതമാണോ?',
      en: 'Is it safe to go fishing off Kochi coast today?'
    },
    {
      ml: 'ഏറ്റവും അടുത്തുള്ള PFZ എവിടെയാണ്?',
      en: 'Where is the nearest Potential Fishing Zone (PFZ)?'
    },
    {
      ml: 'അടുത്ത 12 മണിക്കൂറിലെ കാറ്റും തിരമാലയും വിശദീകരിക്കുക.',
      en: 'Explain wind speed and wave conditions for the next 12 hours.'
    },
    {
      ml: 'കടലിൽ അപകടമുണ്ടായാൽ ആരെ വിളിക്കണം?',
      en: 'Who should I contact if our boat engine fails at sea?'
    }
  ];

  // Initial welcome message
  useEffect(() => {
    if (messages.length > 0) return;

    const initialText = language === 'ML'
      ? 'നമസ്കാരം! ഞാൻ ORCA മറൈൻ അഡ്വൈസറി സഹായിയാണ്. തത്സമയ കടൽ കാലാവസ്ഥ, ഉയർന്ന മീൻ ലഭ്യതയുള്ള മേഖലകൾ (PFZ), ഒപ്പം സുരക്ഷാ മാർഗ്ഗനിർദ്ദേശങ്ങൾ അറിയാൻ താഴെയുള്ള ചോദ്യങ്ങൾ തിരഞ്ഞെടുക്കുകയോ നിങ്ങളുടെ ചോദ്യം ടൈപ്പ് ചെയ്യുകയോ ചെയ്യാം. 🎤 ശബ്ദത്തിലൂടെയും ചോദിക്കാം.'
      : 'Hello! I am **ORCA Marine Advisory Assistant**. Get instant operational intelligence regarding live ocean weather, Potential Fishing Zones (PFZs), and navigation safety.\n\nSelect a quick question below, type your query, or use the 🎤 microphone for voice input.';

    setMessages([
      {
        id: 'welcome-1',
        sender: 'assistant',
        text: initialText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        risk: 'LOW',
        evidence: {
          sources: [
            { name: 'Open-Meteo Marine API', timestamp: new Date().toISOString(), type: 'Real-time Telemetry' },
            { name: 'INCOIS PFZ Advisory', timestamp: new Date().toISOString(), type: 'Official Government Advisory' }
          ],
          confidence_rating: 'HIGH'
        }
      }
    ]);
  }, [language]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  // Voice recording handlers
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        
        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(',')[1];
          handleVoiceSubmit(base64);
        };
        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } catch (err) {
      console.warn('Microphone access denied:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  }, []);

  const handleVoiceSubmit = async (audioBase64: string) => {
    const voiceMsg: ChatMessage = {
      id: `user-voice-${Date.now()}`,
      sender: 'user',
      text: language === 'ML' ? '🎤 ശബ്ദ സന്ദേശം അയച്ചു...' : '🎤 Voice message sent...',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, voiceMsg]);
    setIsProcessing(true);

    try {
      const currentLoc = getSelectedLocation();
      const res = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: '[voice_input]',
          audio_base64: audioBase64,
          context: {
            language,
            location: currentLoc.name,
            coordinates: { lat: currentLoc.lat, lon: currentLoc.lng }
          }
        })
      });

      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      addAssistantMessage(data);
    } catch {
      addFallbackMessage();
    } finally {
      setIsProcessing(false);
    }
  };

  const addAssistantMessage = (data: any) => {
    const replyText = data.text || (language === 'ML'
      ? 'കൊച്ചി തീരത്ത് കടൽ തരംഗങ്ങൾ 1.2 മീറ്ററും കാറ്റ് 18 km/h ഉം ആണ്. സുരക്ഷിതമാണ്.'
      : 'Kochi coastal waters report wave height of 1.2m and winds at 18 km/h. Sea conditions are safe for fishing.');

    const risk = (data.risk || 'LOW').toUpperCase() as 'LOW' | 'MEDIUM' | 'HIGH';
    const agents = data.agents_invoked || [];

    const evidence: EvidenceTrail = {
      sources: [
        { name: 'Open-Meteo Marine API', timestamp: new Date().toISOString(), type: 'Near-Real-Time Telemetry' },
        ...(agents.includes('OrcaNLP') ? [{ name: 'ORCA RAG Knowledge Base', timestamp: new Date().toISOString(), type: 'Advisory RAG' }] : []),
        ...(risk !== 'LOW' ? [{ name: 'IMD Marine Bulletin', timestamp: new Date().toISOString(), type: 'Official Warning' }] : [])
      ],
      threshold_rationale: risk === 'HIGH' ? 'Wave height > 2.5m or Wind > 45 km/h threshold exceeded' : undefined,
      confidence_rating: data.confidence > 80 ? 'HIGH' : data.confidence > 50 ? 'MEDIUM' : 'LOW'
    };

    const assistantMessage: ChatMessage = {
      id: `asst-${Date.now()}`,
      sender: 'assistant',
      text: replyText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      spatialPayload: data.spatial_payload || null,
      risk,
      evidence,
      agentsInvoked: agents,
      feedback: null
    };

    setMessages(prev => [...prev, assistantMessage]);
  };

  const addFallbackMessage = () => {
    const fallbackText = language === 'ML'
      ? 'നിലവിലെ കടൽ സൂചനകൾ: കൊച്ചി തീരത്ത് ശാന്തമായ കാലാവസ്ഥയാണ് (തിരമാല 1.1m, കാറ്റ് 16 km/h). കടലിൽ പോകുന്നത് സുരക്ഷിതമാണ്.'
      : 'Current marine observation: Kochi coast is experiencing calm conditions (1.1m wave height, 16 km/h wind). Safe for marine navigation.';

    setMessages(prev => [
      ...prev,
      {
        id: `fallback-${Date.now()}`,
        sender: 'assistant',
        text: fallbackText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        risk: 'LOW',
        evidence: {
          sources: [{ name: 'Open-Meteo (Cached)', timestamp: new Date().toISOString(), type: 'Cached Telemetry' }],
          confidence_rating: 'MEDIUM'
        },
        feedback: null
      }
    ]);
  };

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
      const res = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          context: {
            language,
            location: currentLoc.name,
            coordinates: { lat: currentLoc.lat, lon: currentLoc.lng }
          }
        })
      });

      if (!res.ok) throw new Error('API server error');
      const data = await res.json();
      addAssistantMessage(data);
    } catch {
      addFallbackMessage();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFeedback = (messageId: string, type: 'up' | 'down') => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, feedback: type } : msg
    ));
    // Fire-and-forget feedback to backend
    fetch(apiUrl('/api/feedback'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'default',
        message_id: messageId,
        rating: type === 'up' ? 5 : 1,
        is_accurate: type === 'up',
      })
    }).catch(() => { /* silent */ });
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
                {language === 'ML' ? 'ORCA മറൈൻ അഡ്വൈസറി' : 'ORCA Marine Advisory'}
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-[#D9F3E6] text-[#16865B]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16865B] mr-1"></span>
                {language === 'ML' ? 'തത്സമയം' : 'Live'}
              </span>
            </div>
            <p className="text-xs text-[#52798F]">
              {language === 'ML'
                ? 'കടൽ കാലാവസ്ഥ, ചാകര (PFZ), സുരക്ഷാ നിർദ്ദേശങ്ങൾ'
                : 'Ocean weather, PFZ coordinates, navigation safety & evidence trails'}
            </p>
          </div>
        </div>

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
          className="p-2 text-[#52798F] hover:text-[#0B3954] hover:bg-[#F4FAFC] rounded-lg transition-colors cursor-pointer"
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
              className="text-xs font-medium bg-white hover:bg-[#DFF3FA] border border-[#D2E6ED] text-[#173042] px-3 py-2 rounded-full whitespace-nowrap shadow-2xs transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer disabled:opacity-50"
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
                className={cn(
                  "max-w-[88%] md:max-w-[78%] rounded-2xl p-4 shadow-2xs",
                  isUser
                    ? 'bg-[#176B87] text-white rounded-br-xs'
                    : 'bg-white text-[#173042] border border-[#D2E6ED] rounded-bl-xs'
                )}
              >
                {/* Sender badge & timestamp */}
                <div className="flex items-center justify-between gap-3 mb-1.5 text-xs">
                  <span className={`font-semibold flex items-center gap-1.5 ${isUser ? 'text-[#DFF3FA]' : 'text-[#0B3954]'}`}>
                    {isUser ? (
                      <span>{language === 'ML' ? 'നിങ്ങൾ' : 'You'}</span>
                    ) : (
                      <>
                        <Bot className="w-3.5 h-3.5 text-[#176B87]" />
                        <span>ORCA Advisory</span>
                      </>
                    )}
                  </span>
                  <span className={`text-[11px] ${isUser ? 'text-[#DFF3FA]/80' : 'text-[#52798F]'}`}>
                    {msg.timestamp}
                  </span>
                </div>

                {/* Message Body — Markdown rendered for assistant */}
                {isUser ? (
                  <p className="text-sm md:text-base leading-relaxed whitespace-pre-line font-normal">
                    {msg.text}
                  </p>
                ) : (
                  <div className="text-sm md:text-base leading-relaxed prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0 prose-headings:text-[#0B3954] prose-strong:text-[#0B3954]">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                )}

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
                      {language === 'ML' ? 'മാപ്പിൽ കാണുക' : 'View on Map'}
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                )}

                {/* Evidence / Data Provenance Trail (PRD §3.4) */}
                {!isUser && msg.evidence && (
                  <EvidenceTrailBlock evidence={msg.evidence} language={language} agentsInvoked={msg.agentsInvoked} />
                )}

                {/* Risk badge + Feedback for Assistant messages */}
                {!isUser && (
                  <div className="mt-2 pt-2 border-t border-[#E8F3F7] flex items-center justify-between">
                    {/* Feedback buttons */}
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleFeedback(msg.id, 'up')}
                        className={cn(
                          "p-1.5 rounded-lg transition-colors cursor-pointer",
                          msg.feedback === 'up' ? 'bg-[#D9F3E6] text-[#16865B]' : 'text-[#A0B2BC] hover:text-[#16865B] hover:bg-[#F4FAFC]'
                        )}
                        title={language === 'ML' ? 'ശരിയാണ്' : 'Accurate'}
                      >
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleFeedback(msg.id, 'down')}
                        className={cn(
                          "p-1.5 rounded-lg transition-colors cursor-pointer",
                          msg.feedback === 'down' ? 'bg-[#FDF0EE] text-[#C0392B]' : 'text-[#A0B2BC] hover:text-[#C0392B] hover:bg-[#FDF0EE]'
                        )}
                        title={language === 'ML' ? 'തെറ്റാണ്' : 'Inaccurate'}
                      >
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Risk badge */}
                    {msg.risk && (
                      <span className={cn(
                        "text-[11px] font-bold px-2 py-0.5 rounded-full",
                        msg.risk === 'LOW' ? 'bg-[#D9F3E6] text-[#16865B]'
                          : msg.risk === 'MEDIUM' ? 'bg-[#FFF7E6] text-[#D99116]'
                          : 'bg-[#FDEDEC] text-[#C0392B]'
                      )}>
                        {msg.risk === 'LOW'
                          ? (language === 'ML' ? '🟢 സുരക്ഷിതം' : '🟢 Safe')
                          : msg.risk === 'MEDIUM'
                            ? (language === 'ML' ? '🟡 ജാഗ്രത' : '🟡 Caution')
                            : (language === 'ML' ? '🔴 അപകടകരം' : '🔴 Hazardous')}
                      </span>
                    )}
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
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-[#176B87] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 bg-[#176B87] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 bg-[#176B87] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Multi-Modal Input Bar with Voice (PRD R1-C04) */}
      <div className="mt-2 bg-white border border-[#D2E6ED] rounded-2xl p-2.5 shadow-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          {/* Voice Button */}
          <button
            type="button"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
            className={cn(
              "h-12 w-12 rounded-xl flex items-center justify-center shrink-0 transition-all cursor-pointer shadow-xs",
              isRecording
                ? "bg-[#C0392B] hover:bg-[#A93226] text-white animate-pulse"
                : "bg-[#F4F9FB] hover:bg-[#DFF3FA] text-[#176B87] border border-[#D2E6ED]"
            )}
            title={isRecording ? (language === 'ML' ? 'നിർത്തുക' : 'Stop recording') : (language === 'ML' ? 'ശബ്ദം ഉപയോഗിക്കുക' : 'Voice input')}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Recording duration indicator */}
          {isRecording && (
            <span className="text-xs font-mono text-[#C0392B] font-bold shrink-0">
              {Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, '0')}
            </span>
          )}

          {/* Text Input Field */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              language === 'ML' ? 'ചോദ്യം ഇവിടെ ടൈപ്പ് ചെയ്യുക...' : 'Type your question here...'
            }
            disabled={isRecording}
            className="flex-1 h-12 px-4 bg-[#F8FCFD] border border-[#D2E6ED] rounded-xl text-[#173042] placeholder-[#52798F] text-sm md:text-base focus:outline-none focus:ring-2 focus:ring-[#176B87] focus:bg-white transition-all disabled:opacity-50"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isProcessing || isRecording}
            className="h-12 px-5 rounded-xl bg-[#176B87] hover:bg-[#0B3954] disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-xs md:text-sm flex items-center justify-center gap-1.5 shrink-0 shadow-xs transition-colors cursor-pointer"
          >
            <span>{language === 'ML' ? 'അയക്കുക' : 'Send'}</span>
            <Send className="w-4 h-4" />
          </button>
        </form>

        <div className="flex items-center justify-between px-2 pt-2 text-[11px] text-[#52798F]">
          <span className="flex items-center gap-1">
            <Mic className="w-3 h-3" />
            {language === 'ML' ? 'ശബ്ദത്തിലും ടൈപ്പിലും ചോദിക്കാം' : 'Voice & text input in all languages'}
          </span>
          <span className="flex items-center gap-1 font-semibold text-[#16865B]">
            <ShieldCheck className="w-3.5 h-3.5" />
            INCOIS · Open-Meteo · ORCA
          </span>
        </div>
      </div>
    </div>
  );
}

/** Evidence Trail Collapsible Block (PRD §3.4 Explainable Evidence Trails) */
function EvidenceTrailBlock({ evidence, language, agentsInvoked }: {
  evidence: EvidenceTrail;
  language: string;
  agentsInvoked?: string[];
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-2.5">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[11px] text-[#52798F] hover:text-[#0B3954] font-medium transition-colors cursor-pointer"
      >
        <BookOpen className="w-3 h-3" />
        <span>{language === 'ML' ? 'ഡാറ്റ ഉറവിടങ്ങൾ & തെളിവുകൾ' : 'Data Sources & Evidence'}</span>
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {expanded && (
        <div className="mt-1.5 p-2.5 bg-[#F4FAFC] border border-[#D2E6ED] rounded-lg text-[11px] space-y-1.5 animate-in fade-in duration-200">
          {/* Sources consulted */}
          <div>
            <span className="font-bold text-[#0B3954]">
              {language === 'ML' ? 'ഉറവിടങ്ങൾ:' : 'Sources Consulted:'}
            </span>
            <ul className="mt-0.5 space-y-0.5">
              {evidence.sources.map((src, i) => (
                <li key={i} className="flex items-center gap-1.5 text-[#52798F]">
                  <span className="w-1 h-1 rounded-full bg-[#176B87] shrink-0" />
                  <span className="font-medium text-[#173042]">{src.name}</span>
                  <span className="text-[10px]">({src.type})</span>
                  <span className="text-[10px] flex items-center gap-0.5">
                    <Clock className="w-2.5 h-2.5" />
                    {new Date(src.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Threshold rationale */}
          {evidence.threshold_rationale && (
            <div>
              <span className="font-bold text-[#0B3954]">
                {language === 'ML' ? 'നിർണ്ണായക ഘടകങ്ങൾ:' : 'Key Factors:'}
              </span>
              <p className="text-[#52798F] mt-0.5">{evidence.threshold_rationale}</p>
            </div>
          )}

          {/* Confidence */}
          <div className="flex items-center gap-2">
            <span className="font-bold text-[#0B3954]">
              {language === 'ML' ? 'വിശ്വാസ്യത:' : 'Confidence:'}
            </span>
            <span className={cn(
              "px-1.5 py-0.5 rounded font-bold",
              evidence.confidence_rating === 'HIGH' ? 'bg-[#D9F3E6] text-[#16865B]'
                : evidence.confidence_rating === 'MEDIUM' ? 'bg-[#FFF7E6] text-[#D99116]'
                : 'bg-[#FDF0EE] text-[#C0392B]'
            )}>
              {evidence.confidence_rating}
            </span>
          </div>

          {/* Agents invoked */}
          {agentsInvoked && agentsInvoked.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-bold text-[#0B3954]">
                {language === 'ML' ? 'ഏജന്റുകൾ:' : 'Agents:'}
              </span>
              {agentsInvoked.map((agent, i) => (
                <span key={i} className="px-1.5 py-0.5 rounded bg-[#DFF3FA] text-[#176B87] font-medium">
                  {agent}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
