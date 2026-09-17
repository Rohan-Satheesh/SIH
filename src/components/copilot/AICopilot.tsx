import React, { useState } from 'react';
import { Send, BrainCircuit, Cpu, CheckCircle2, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import ProvenanceModal from '@/components/hud/ProvenanceModal';
import { getSelectedLocation } from '@/services/liveMarineService';

interface StructuredOutput {
  queryText?: string;
  agentsInvoked: string[];
  recommendation: string;
  confidence: number;
  risk: 'LOW' | 'MEDIUM' | 'HIGH';
  evidence: string[];
  location?: string;
  actionZone?: string;
}

interface Message {
  id: string;
  role: 'user' | 'agent';
  content?: string;
  structured?: StructuredOutput;
  timestamp: string;
}

const initialMessages: Message[] = [];

export default function AICopilot() {
  const [sessionId] = useState<string>(() => `ses-${crypto.randomUUID().slice(0, 8)}`);
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [whyModalOpen, setWhyModalOpen] = useState(false);
  const [currentWhyTitle, setCurrentWhyTitle] = useState('');

  const quickPrompts = [
    "Safe PFZ near Kochi tomorrow",
    "Evaluate cyclone risk for Sagar Kanya",
    "Optimize route Mumbai to Singapore"
  ];

  const handleSend = async (customQuery?: string) => {
    const query = customQuery || input;
    if (!query.trim() || isProcessing) return;

    const userMsg: Message = {
      id: `user-${crypto.randomUUID()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString().substring(11, 16) + ' UTC'
    };

    setMessages(prev => [...prev, userMsg]);
    if (!customQuery) setInput('');
    setIsProcessing(true);

    try {
      const history = messages
        .filter(m => m.content || m.structured?.recommendation)
        .map(m => ({
          role: m.role,
          content: m.content || m.structured?.recommendation || ''
        }));

      const currentLoc = getSelectedLocation();
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: query,
          session_id: sessionId,
          history,
          context: {
            location: currentLoc.name,
            coordinates: { lat: currentLoc.lat, lon: currentLoc.lng }
          }
        })
      });

      const data = await res.json();
      
      const structuredResult: StructuredOutput = {
        queryText: query,
        agentsInvoked: Array.isArray(data.agents_invoked) ? data.agents_invoked : [],
        recommendation: data.text || (data.location ? `Operational Advisory: ${data.location}` : 'Marine intelligence analysis complete.'),
        confidence: typeof data.confidence === 'number' ? data.confidence : 0,
        risk: (data.risk || 'LOW') as 'LOW' | 'MEDIUM' | 'HIGH',
        evidence: Array.isArray(data.conditions) ? data.conditions : [],
        location: data.location || undefined
      };

      const agentMsg: Message = {
        id: `agent-${crypto.randomUUID()}`,
        role: 'agent',
        structured: structuredResult,
        timestamp: new Date().toISOString().substring(11, 16) + ' UTC'
      };

      setMessages(prev => [...prev, agentMsg]);
    } catch {
      const agentMsg: Message = {
        id: `agent-${crypto.randomUUID()}`,
        role: 'agent',
        content: 'Live intelligence API is unavailable. No recommendation was generated.',
        timestamp: new Date().toISOString().substring(11, 16) + ' UTC'
      };

      setMessages(prev => [...prev, agentMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOpenWhy = (title: string) => {
    setCurrentWhyTitle(title);
    setWhyModalOpen(true);
  };

  return (
    <div className="w-full h-full flex flex-col bg-[#070D18] select-none font-sans">
      
      {/* Console Header */}
      <div className="p-3 border-b border-slate-800 bg-[#091120] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <BrainCircuit className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-xs font-semibold text-white">
              AI Copilot Console
            </h2>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 text-[11px] text-slate-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Live agent status unavailable</span>
        </div>
      </div>

      {/* Chat Messages Feed */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin">
        {messages.map((msg) => {
          if (msg.role === 'user') {
            return (
              <div key={msg.id} className="flex flex-col items-end space-y-1">
                <div className="bg-cyan-600 text-white text-xs px-3 py-2 rounded-xl rounded-tr-xs max-w-[85%] shadow-sm">
                  {msg.content}
                </div>
                <span className="text-[10px] text-slate-500 font-mono">{msg.timestamp}</span>
              </div>
            );
          }

          const s = msg.structured;
          if (!s) return null;

          return (
            <div key={msg.id} className="space-y-2 text-xs bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 shadow-sm">
              
              {/* Header: Query & Agents Invoked */}
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <div className="flex flex-wrap gap-1">
                  {s.agentsInvoked.map((agent, i) => (
                    <span key={i} className="text-[10px] bg-slate-800/80 text-slate-300 px-1.5 py-0.5 rounded font-medium">
                      {agent}
                    </span>
                  ))}
                </div>
                <span className="text-[10px] text-slate-500 font-mono">{msg.timestamp}</span>
              </div>

              {/* Recommendation Box */}
              <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                <span className="text-[10px] text-cyan-400 uppercase font-bold tracking-wider block">
                  Recommendation
                </span>
                <p className="text-xs font-semibold text-white mt-0.5 leading-snug">
                  {s.recommendation}
                </p>
              </div>

              {/* Confidence & Risk */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 bg-slate-800/50 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Confidence</span>
                  <span className="font-bold text-emerald-400 font-mono text-sm">{s.confidence}%</span>
                </div>
                <div className="p-2 bg-slate-800/50 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Risk Rating</span>
                  <span className={cn("font-bold text-sm", s.risk === 'LOW' ? 'text-emerald-400' : s.risk === 'MEDIUM' ? 'text-amber-400' : 'text-rose-400')}>
                    {s.risk} RISK
                  </span>
                </div>
              </div>

              {/* Evidence Checklist */}
              {s.evidence && s.evidence.length > 0 && (
                <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block">
                    Telemetry Evidence
                  </span>
                  {s.evidence.map((item, idx) => (
                    <div key={idx} className="flex items-start space-x-2 text-[11px] text-slate-300">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                      <span className="leading-tight">{item}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Actions Footer */}
              <div className="pt-2 border-t border-slate-800/80">
                <button 
                  onClick={() => handleOpenWhy(s.recommendation)}
                  className="w-full py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 rounded-lg text-xs font-medium transition-colors flex items-center justify-center space-x-1.5 cursor-pointer"
                >
                  <Info className="w-3.5 h-3.5" />
                  <span>Explain Data Provenance</span>
                </button>
              </div>
            </div>
          );
        })}

        {isProcessing && (
          <div className="p-2.5 rounded-lg bg-slate-900 border border-cyan-500/30 flex items-center space-x-2 text-cyan-400 text-xs">
            <Cpu className="w-3.5 h-3.5 animate-spin" />
            <span className="animate-pulse">Consulting multi-agent swarm...</span>
          </div>
        )}
      </div>

      {/* Quick Action Prompt Pills */}
      <div className="p-2.5 border-t border-slate-800/80 bg-[#091120] flex flex-wrap gap-1.5">
        {quickPrompts.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="text-[11px] px-2.5 py-1 rounded-full bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/60 transition-colors truncate max-w-full text-left cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-slate-800 bg-[#070D18]">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask AI Copilot..."
            disabled={isProcessing}
            className="w-full bg-slate-900 border border-slate-700 focus:border-cyan-500 rounded-lg pl-3 pr-10 py-2 text-xs text-white placeholder-slate-500 focus:outline-none transition-colors"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isProcessing}
            className="absolute right-1.5 p-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-md transition-colors disabled:opacity-40 cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Provenance Modal */}
      <ProvenanceModal
        isOpen={whyModalOpen}
        onClose={() => setWhyModalOpen(false)}
        recommendation={currentWhyTitle || 'Marine Copilot Intelligence Decision'}
      />
    </div>
  );
}
