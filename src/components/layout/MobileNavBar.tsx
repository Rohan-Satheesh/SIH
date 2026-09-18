import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, CloudSun, Waves, Fish, MessageSquare, ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';

export default function MobileNavBar() {
  const { t } = useLanguage();

  const navItems = [
    { label: t('navAssistant') || 'AI Assistant', path: '/', icon: MessageSquare },
    { label: t('navHome') || 'Dashboard', path: '/dashboard', icon: Home },
    { label: t('navWeather'), path: '/weather', icon: CloudSun },
    { label: t('navZones'), path: '/zones', icon: Fish },
    { label: t('navSafety'), path: '/safety', icon: ShieldAlert, alert: true },
  ];

  return (
    <nav 
      aria-label="Mobile Bottom Navigation"
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-[#D8E5EB] shadow-[0_-4px_20px_rgba(11,57,84,0.08)] flex items-center justify-around px-1 py-1.5 safe-area-pb"
    >
      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => cn(
              "flex flex-col items-center justify-center flex-1 py-1 px-1 rounded-xl transition-all min-h-[50px] touch-manipulation",
              isActive 
                ? "text-[#0B3954] font-bold bg-[#DFF3FA]/70" 
                : "text-[#5B7282] hover:text-[#0B3954] font-medium"
            )}
          >
            {({ isActive }) => (
              <>
                <div className={cn(
                  "p-1 rounded-lg transition-transform relative",
                  isActive && "scale-110"
                )}>
                  <Icon className={cn("w-5 h-5", isActive ? "text-[#176B87]" : item.alert ? "text-[#C0392B]" : "text-[#5B7282]")} />
                  {item.alert && !isActive && (
                    <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-[#C0392B] rounded-full animate-pulse" />
                  )}
                </div>
                <span className={cn("text-[10px] leading-tight truncate mt-0.5 tracking-tight", item.alert && !isActive && "text-[#C0392B]")}>
                  {item.label}
                </span>
              </>
            )}
          </NavLink>
        );
      })}
    </nav>
  );
}
