import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import KPIBar from '../components/dashboard/KPIBar';
import MarineMap from '../components/map/MarineMap';
import AICopilot from '../components/copilot/AICopilot';
import { 
  ChevronRight, 
  ChevronLeft,
  Radio,
  MapPin
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function CommandCenter() {
  const context = useOutletContext<{ isScanning?: boolean; setIsScanning?: (val: boolean) => void }>() || {};
  const [isScanning, setIsScanning] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(true);

  return (
    <div className="flex flex-col h-full overflow-hidden relative select-none font-sans bg-[#F8FCFD]">
      
      {/* Top Operations KPI Stream Bar */}
      <div className="relative z-30 flex-shrink-0">
        <KPIBar />
      </div>

      {/* Main Operations Split: Dominant Map + Dockable AI Copilot */}
      <div className="flex flex-1 overflow-hidden relative z-10">
        
        {/* Full-Screen Map Centerpiece */}
        <div className="flex-1 relative flex flex-col h-full bg-[#F8FCFD] overflow-hidden">
          
          {/* Main Interactive Map */}
          <div className="flex-1 relative w-full h-full">
            <MarineMap 
              isScanning={isScanning || context.isScanning}
              onScanComplete={() => {
                setIsScanning(false);
                if (context.setIsScanning) context.setIsScanning(false);
              }}
            />
          </div>

          {/* Clean Floating Telemetry Badge (Bottom Left) */}
          <div className="absolute bottom-3.5 left-3.5 z-10 hidden md:flex items-center space-x-2 bg-white/95 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-[#D8E5EB] text-xs shadow-sm text-[#173042]">
            <span className="font-bold text-[#176B87]">Spatial Telemetry</span>
            <span className="text-[#A0B2BC]">•</span>
            <span className="text-[#5B7282]">Indian EEZ Live</span>
            <span className="text-[#A0B2BC]">•</span>
            <span className="text-[#16865B] font-semibold">AIS Transponder Feed</span>
          </div>
        </div>

        {/* Right Collapsible Dock: AI Marine Copilot */}
        <div 
          className={cn(
            "transition-all duration-300 border-l border-[#D8E5EB] bg-white flex flex-col relative z-20 shadow-xs",
            copilotOpen ? "w-96" : "w-0 overflow-hidden"
          )}
        >
          {/* Copilot Dock Toggle Button */}
          <button 
            onClick={() => setCopilotOpen(!copilotOpen)}
            className="absolute -left-7 top-4 z-30 p-1.5 bg-white text-[#176B87] border border-[#D8E5EB] rounded-l-lg hover:bg-[#F4F9FB] transition-colors shadow-xs cursor-pointer"
            title={copilotOpen ? "Collapse Copilot" : "Expand Copilot"}
          >
            {copilotOpen ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>

          {copilotOpen && (
            <div className="h-full flex flex-col">
              <AICopilot />
            </div>
          )}
        </div>

        {/* Floating open button when copilot is collapsed */}
        {!copilotOpen && (
          <button 
            onClick={() => setCopilotOpen(true)}
            className="absolute right-4 top-4 z-20 flex items-center space-x-2 px-3.5 py-2 bg-white/95 backdrop-blur-md text-[#176B87] border border-[#D8E5EB] rounded-xl hover:bg-[#F4F9FB] transition-all shadow-md text-xs font-bold cursor-pointer"
          >
            <Radio className="w-4 h-4 text-[#176B87] animate-pulse" />
            <span>AI Copilot</span>
          </button>
        )}
      </div>
    </div>
  );
}
