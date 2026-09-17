import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Ship, 
  Anchor, 
  Database, 
  Command, 
  Radar,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

interface CommandItem {
  id: string;
  category: string;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  action: () => void;
  shortcut?: string;
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const commandList: CommandItem[] = [
    {
      id: 'cmd-dashboard',
      category: 'Navigation',
      title: 'Command Center',
      subtitle: 'Mission control map, layers, and copilot',
      icon: Command,
      action: () => { navigate('/dashboard'); onClose(); },
      shortcut: 'G D'
    },
    {
      id: 'cmd-fleet',
      category: 'Operations',
      title: 'Run Fleet Optimization',
      subtitle: 'Quantum-inspired multi-objective routing (Fuel & CO₂)',
      icon: Ship,
      action: () => { navigate('/fleet'); onClose(); },
      shortcut: 'G F'
    },
    {
      id: 'cmd-fisherman',
      category: 'Mode Switch',
      title: 'Switch to Fisherman Mode',
      subtitle: 'High-contrast mobile-first outdoor interface',
      icon: Anchor,
      action: () => { navigate('/fisherman'); onClose(); },
      shortcut: 'G M'
    },
    {
      id: 'cmd-data-sources',
      category: 'Data Core',
      title: 'Data Sources Health',
      subtitle: 'INCOIS, MOSDAC/ISRO, IMD, Copernicus Marine sync telemetry',
      icon: Database,
      action: () => { navigate('/data-sources'); onClose(); }
    },
  ];

  const filteredCommands = commandList.filter(cmd => 
    cmd.title.toLowerCase().includes(query.toLowerCase()) ||
    cmd.subtitle.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev < filteredCommands.length - 1 ? prev + 1 : 0));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : filteredCommands.length - 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-start justify-center pt-24 bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl bg-[#07111F] border border-cyan-500/30 rounded-xl shadow-[0_0_50px_rgba(0,210,255,0.2)] overflow-hidden font-mono flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Search Header */}
        <div className="flex items-center px-4 border-b border-cyan-500/20 bg-[#0A1628]">
          <Search className="w-5 h-5 text-cyan-400 mr-3 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0); }}
            placeholder="Type a command or search vessels, PFZ, alerts, optimization..."
            className="w-full py-4 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <kbd className="hidden sm:inline-flex items-center px-2 py-0.5 text-[10px] text-slate-400 bg-slate-800/80 rounded border border-slate-700">
            ESC to close
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-400 font-mono">
              <Radar className="w-8 h-8 text-cyan-400/40 mx-auto mb-2 animate-spin-slow" />
              No matching operations or telemetry found.
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  onClick={() => cmd.action()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-150",
                    isSelected 
                      ? "bg-cyan-500/15 border border-cyan-500/40 text-white" 
                      : "text-slate-300 hover:bg-slate-800/50 border border-transparent"
                  )}
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className={cn(
                      "w-8 h-8 rounded flex items-center justify-center border",
                      isSelected 
                        ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40" 
                        : "bg-[#0A1628] text-slate-400 border-slate-700/50"
                    )}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-white tracking-wide">{cmd.title}</span>
                        <span className="text-[9px] px-1.5 py-0.2 bg-slate-800 text-slate-400 rounded uppercase">
                          {cmd.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">{cmd.subtitle}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0 ml-4">
                    {cmd.shortcut && (
                      <span className="text-[10px] text-slate-500 font-mono hidden md:inline">{cmd.shortcut}</span>
                    )}
                    {isSelected && <ArrowRight className="w-4 h-4 text-cyan-400" />}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-[#050B14] border-t border-cyan-500/10 flex items-center justify-between text-[10px] text-slate-400">
          <div className="flex items-center space-x-3">
            <span>Use <kbd className="text-slate-300">↑</kbd> <kbd className="text-slate-300">↓</kbd> to navigate</span>
            <span><kbd className="text-slate-300">Enter</kbd> to select</span>
          </div>
          <span className="text-cyan-400/80 font-mono">NEERMITRA COMMAND // CTRL+K</span>
        </div>
      </div>
    </div>
  );
}
