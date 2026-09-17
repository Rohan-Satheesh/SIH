import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import MobileNavBar from './MobileNavBar';
import { LanguageProvider } from '@/contexts/LanguageContext';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorBoundaryState> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 max-w-2xl mx-auto my-8 bg-white border border-[#F5C6CB] rounded-2xl shadow-sm text-[#173042]">
          <div className="flex items-center space-x-3 text-[#C0392B] mb-2">
            <span className="text-base font-bold">⚠️ Module Render Notice</span>
          </div>
          <p className="text-xs text-[#5B7282] mb-3">
            An unexpected error occurred while rendering this module. All other platform navigation remains operational.
          </p>
          <pre className="text-xs font-mono bg-[#FDF0EE] text-[#C0392B] p-3 rounded-xl border border-[#F5C6CB] overflow-auto max-h-40 mb-4 whitespace-pre-wrap">
            {this.state.error?.message || String(this.state.error)}
          </pre>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-[#176B87] hover:bg-[#0B3954] text-white text-xs font-bold rounded-xl transition-all cursor-pointer"
          >
            Retry Loading
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function AppShell() {
  const [isScanning, setIsScanning] = useState(false);

  return (
    <LanguageProvider>
      <div className="min-h-screen flex flex-col bg-[#F8FCFD] text-[#173042] font-sans antialiased selection:bg-[#176B87]/20 selection:text-[#0B3954]">
        
        {/* Top App Header */}
        <TopBar />

        <div className="flex flex-1 overflow-hidden relative">
          {/* Desktop Left Navigation Rail */}
          <Sidebar />

          {/* Main Content Viewport */}
          <main className="flex-1 overflow-y-auto relative pb-20 md:pb-6">
            <ErrorBoundary>
              <Outlet context={{ isScanning, setIsScanning }} />
            </ErrorBoundary>
          </main>
        </div>

        {/* Mobile Bottom Navigation Bar (Fixed for < 768px screens) */}
        <MobileNavBar />
      </div>
    </LanguageProvider>
  );
}
