import React from 'react';
import { Database, BrainCircuit, ShieldAlert, Cpu, CheckCircle2, ArrowDown, X, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Factor {
  label: string;
  weight: string;
  detail: string;
  status: 'positive' | 'neutral' | 'warning';
}

interface ProvenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  recommendation?: string;
  factors?: Factor[];
}

const defaultFactors: Factor[] = [];

export default function ProvenanceModal({
  isOpen,
  onClose,
  title = 'AI Provenance & Lineage Explainability',
  subtitle = 'Data lineage & multi-agent reasoning trace',
  recommendation = 'No live recommendation available',
  factors = defaultFactors
}: ProvenanceModalProps) {
  if (!isOpen) return null;

  const lineageNodes = [
    { title: 'Satellite & Maritime Sources', desc: 'MOSDAC (ISRO), INCOIS, IMD, AIS Stream', icon: Database, color: 'text-cyan-400 border-cyan-500/20 bg-slate-900/90' },
    { title: 'Specialist AI Agents', desc: 'Ocean Analytics, Weather Intelligence, Marine Data Discovery', icon: BrainCircuit, color: 'text-blue-400 border-blue-500/20 bg-slate-900/90' },
    { title: 'Risk & Safety Engine', desc: 'Dynamic boundary assessment, wave & wind limits checked', icon: ShieldAlert, color: 'text-emerald-400 border-emerald-500/20 bg-slate-900/90' },
    { title: 'Quantum-Inspired Optimizer', desc: 'Pareto-optimal trade-off evaluated for route & fuel', icon: Cpu, color: 'text-amber-400 border-amber-500/20 bg-slate-900/90' },
  ];

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl bg-[#091120] border border-slate-800 rounded-xl shadow-2xl overflow-hidden font-sans flex flex-col max-h-[90vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-800 bg-[#070D18] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Info className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-sm font-bold text-white">{title}</h2>
              <p className="text-xs text-slate-400">{subtitle}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto space-y-5">
          {/* Target Result */}
          <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
            <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider block mb-1">
              Decision Target
            </span>
            <div className="text-base font-bold text-white">
              {recommendation}
            </div>
          </div>

          {/* Lineage Pipeline */}
          <div>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5">
              1. Multi-Agent Lineage Pipeline
            </h3>
            <div className="space-y-2">
              {lineageNodes.map((node, idx) => (
                <React.Fragment key={idx}>
                  <div className={cn("p-3 rounded-lg border flex items-center space-x-3", node.color)}>
                    <node.icon className="w-5 h-5 flex-shrink-0 text-cyan-400" />
                    <div className="flex-1">
                      <h4 className="text-xs font-semibold text-white">{node.title}</h4>
                      <p className="text-[11px] text-slate-400">{node.desc}</p>
                    </div>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  </div>
                  {idx < lineageNodes.length - 1 && (
                    <div className="flex justify-center py-0.5">
                      <ArrowDown className="w-3.5 h-3.5 text-slate-600" />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Contributing Factors & Weights */}
          <div>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5">
              2. Contributing Satellite & Physics Factors
            </h3>
            <div className="space-y-2">
              {factors.map((factor, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-3 text-xs">
                  <div>
                    <span className="font-semibold text-white block text-xs">{factor.label}</span>
                    <span className="text-[11px] text-slate-400 block mt-0.5">{factor.detail}</span>
                  </div>
                  <span className="font-bold text-emerald-400 font-mono text-xs px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 flex-shrink-0">
                    {factor.weight}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-slate-800 bg-[#070D18] flex items-center justify-between text-xs text-slate-400">
          <span className="text-[11px]">Provenance Hash: <span className="font-mono text-cyan-400">0x8f3c...b291</span></span>
          <button 
            onClick={onClose}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium transition-colors cursor-pointer"
          >
            Close Trace
          </button>
        </div>
      </div>
    </div>
  );
}
