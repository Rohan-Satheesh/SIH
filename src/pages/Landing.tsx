import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Particles from '../components/ui/Particles';
import { 
  Compass, 
  BrainCircuit, 
  ShieldCheck, 
  Cpu, 
  ArrowRight, 
  Waves, 
  Anchor,
  Database
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Landing() {
  const navigate = useNavigate();
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 });
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setMousePos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  const pipelineStages = [
    { title: 'DATA STREAMS', subtitle: 'MOSDAC • INCOIS • IMD • AIS', icon: Database, color: 'text-cyan-400 border-cyan-500/30' },
    { title: 'AI SPECIALISTS', subtitle: '9 Multi-Agent Swarm', icon: BrainCircuit, color: 'text-blue-400 border-blue-500/30' },
    { title: 'INTELLIGENCE', subtitle: 'PFZ • Currents • Swell', icon: Waves, color: 'text-emerald-400 border-emerald-500/30' },
    { title: 'RISK ENGINE', subtitle: 'EEZ Safety & Physics', icon: ShieldCheck, color: 'text-amber-400 border-amber-500/30' },
    { title: 'DECISION / QUBO', subtitle: 'Pareto Fleet Optimization', icon: Cpu, color: 'text-cyan-300 border-cyan-400/40' }
  ];

  return (
    <div 
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="min-h-screen bg-[#050B14] text-slate-100 relative overflow-hidden flex flex-col font-sans select-none"
    >
      {/* Spotlight Cursor Glow Effect */}
      <div 
        className="pointer-events-none absolute -inset-px opacity-40 transition-opacity duration-300 z-10"
        style={{
          background: `radial-gradient(600px circle at ${mousePos.x}px ${mousePos.y}px, rgba(0, 210, 255, 0.12), transparent 80%)`
        }}
      />

      {/* Living Ocean Particles */}
      <div className="absolute inset-0 z-0 opacity-80 pointer-events-none">
        <Particles
          particleColors={["#00D2FF", "#06B6D4", "#10B981", "#38BDF8", "#67E8F9"]}
          particleCount={260}
          particleSpread={14}
          speed={0.12}
          particleBaseSize={110}
          moveParticlesOnHover={true}
          particleHoverFactor={1.2}
          alphaParticles={true}
          disableRotation={false}
        />
      </div>

      {/* Background Grid & Scanline */}
      <div className="absolute inset-0 bg-ocean-grid opacity-25 pointer-events-none z-[1]" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#050B14] via-transparent to-[#050B14]/80 pointer-events-none z-[1]" />

      {/* Top Navigation */}
      <header className="relative z-20 h-16 border-b border-slate-800/80 bg-[#070D18]/80 backdrop-blur-md flex items-center justify-between px-6 lg:px-12 font-sans">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <Compass className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <span className="text-base font-bold tracking-wide text-white">NEERMITRA</span>
            <span className="text-[10px] text-cyan-400 font-medium block">Marine Intelligence OS</span>
          </div>
        </div>

        <div className="hidden md:flex items-center space-x-2 text-xs px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-mono text-cyan-400">Live telemetry</span>
          <span className="text-slate-600">•</span>
          <span className="text-slate-400">ISRO & INCOIS Ingest</span>
        </div>

        <div className="flex items-center space-x-2.5">
          <button 
            onClick={() => navigate('/fisherman')}
            className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20 transition-all cursor-pointer"
          >
            <Anchor className="w-3.5 h-3.5" />
            <span>Fisherman Mode</span>
          </button>
          <button 
            onClick={() => navigate('/dashboard')}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-sm cursor-pointer"
          >
            <span>Launch OS</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-20 flex-1 flex flex-col items-center justify-center px-4 py-12 text-center max-w-5xl mx-auto space-y-7">
        
        {/* Live Status Pill */}
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-900/90 border border-slate-800 text-xs text-slate-300 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-medium">Indian Ocean Telemetry Live</span>
          <span className="text-slate-600">•</span>
          <span className="text-slate-400 font-mono">AIS status on dashboard</span>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-tight">
            NEERMITRA
          </h1>
          <h2 className="text-lg sm:text-2xl md:text-3xl font-bold bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-400 bg-clip-text text-transparent max-w-3xl mx-auto">
            Intelligence for Safer Seas. Optimization for Greener Fleets.
          </h2>
          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto font-normal leading-relaxed">
            An ISRO-calibrated marine intelligence operating system combining multi-satellite earth observation, physics-informed ocean analytics, and quantum-inspired fleet routing.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-1">
          <button 
            onClick={() => navigate('/dashboard')}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-cyan-500 text-slate-950 font-bold text-xs hover:bg-cyan-400 transition-all shadow-md flex items-center justify-center space-x-2 cursor-pointer"
          >
            <Compass className="w-4 h-4" />
            <span>Launch Command Center</span>
          </button>
          
          <button 
            onClick={() => navigate('/fleet')}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg border border-slate-700 bg-slate-900/90 text-white font-semibold text-xs hover:bg-slate-800 hover:border-cyan-500/40 transition-all flex items-center justify-center space-x-2 cursor-pointer"
          >
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Run Fleet Optimizer</span>
          </button>
        </div>

        {/* The 5-Stage Mission Control Flow */}
        <div className="pt-6 w-full">
          <div className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase mb-3">
            Intelligence Workflow Pipeline
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 max-w-4xl mx-auto">
            {pipelineStages.map((stage, idx) => {
              const Icon = stage.icon;
              return (
                <div 
                  key={idx} 
                  className={cn(
                    "p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-left flex flex-col justify-between group hover:border-cyan-500/40 transition-all shadow-sm"
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] text-slate-500 font-mono font-semibold">0{idx + 1}</span>
                    <Icon className="w-4 h-4 text-cyan-400 group-hover:scale-105 transition-transform" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white">{stage.title}</h3>
                    <p className="text-[10px] text-slate-400 truncate mt-0.5">{stage.subtitle}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      {/* Live Telemetry Footer Strip */}
      <footer className="relative z-20 h-12 border-t border-slate-800 bg-[#070D18]/90 backdrop-blur-md flex items-center justify-between px-6 text-xs select-none">
        <div className="flex items-center space-x-5 overflow-x-auto scrollbar-none py-1 text-slate-400">
          <div className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-[11px]">SST: awaiting live observation</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span className="text-[11px]">Wave: 1.2m Safe</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-[11px]">9 AI Agents Synchronized</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span className="text-[11px]">QUBO Solver Ready</span>
          </div>
        </div>

        <div className="hidden lg:flex items-center space-x-2 text-[11px] text-slate-500">
          <span>Coordinated with INCOIS & MOSDAC</span>
        </div>
      </footer>
    </div>
  );
}
