import React, { useState, useEffect } from 'react';
import { Radar, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ScanEffectProps {
  isScanning: boolean;
  onScanComplete?: () => void;
  className?: string;
}

export default function ScanEffect({ isScanning, onScanComplete, className = '' }: ScanEffectProps) {
  const [detectionIndex, setDetectionIndex] = useState(0);

  const detections = [
    { label: 'LIVE LAYER REFRESH', detail: 'Refreshing connected spatial layers', color: 'text-cyan-400' },
    { label: 'PROVIDER STATUS CHECK', detail: 'Verifying available telemetry providers', color: 'text-emerald-400' },
    { label: 'AIS STATUS', detail: 'Live status shown on dashboard', color: 'text-cyan-400' },
  ];

  useEffect(() => {
    if (isScanning) {
      setDetectionIndex(0);
      const interval = setInterval(() => {
        setDetectionIndex(prev => {
          if (prev >= detections.length - 1) {
            clearInterval(interval);
            setTimeout(() => {
              if (onScanComplete) onScanComplete();
            }, 1000);
            return prev;
          }
          return prev + 1;
        });
      }, 700);

      return () => clearInterval(interval);
    }
  }, [isScanning]);

  if (!isScanning) return null;

  return (
    <div className={cn("absolute inset-0 pointer-events-none z-30 overflow-hidden", className)}>
      {/* Scanline Sweep */}
      <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_20px_#00D2FF] animate-scanline" />

      {/* Grid Pulse Overlay */}
      <div className="absolute inset-0 bg-cyan-500/5 backdrop-blur-[1px] transition-opacity duration-300" />

      {/* Floating Detection Telemetry Box */}
      <div className="absolute top-6 right-6 bg-[#07111F]/95 border border-cyan-400/50 rounded-lg p-3 shadow-[0_0_30px_rgba(0,210,255,0.3)] font-mono max-w-sm pointer-events-auto tech-corner animate-in fade-in zoom-in duration-200">
        <div className="flex items-center space-x-2 border-b border-cyan-500/30 pb-2 mb-2">
          <Radar className="w-4 h-4 text-cyan-400 animate-spin" />
          <span className="text-xs font-bold text-cyan-300 uppercase tracking-widest">
            SATELLITE RADAR SWEEP ACTIVE
          </span>
        </div>

        <div className="space-y-2">
          {detections.slice(0, detectionIndex + 1).map((item, idx) => (
            <div key={idx} className="flex items-start space-x-2 text-[11px] animate-in fade-in slide-in-from-right-4 duration-300">
              <Sparkles className="w-3 h-3 text-cyan-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className={cn("font-bold uppercase tracking-wider", item.color)}>
                  {item.label}
                </p>
                <p className="text-[10px] text-slate-400 font-normal">
                  {item.detail}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
