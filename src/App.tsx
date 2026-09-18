import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';

import HomeDashboard from './pages/HomeDashboard';
import WeatherView from './pages/WeatherView';
import SeaConditionsView from './pages/SeaConditionsView';
import FishermanMode from './pages/FishermanMode';
import { AssistantView } from './pages/AssistantView';
import { SafetyView } from './pages/SafetyView';
import FleetOptimizer from './pages/FleetOptimizer';
import DataSources from './pages/DataSources';
import CommandCenter from './pages/CommandCenter';
import Landing from './pages/Landing';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Operational Marine App routes wrapped in sunlight-readable AppShell */}
        <Route element={<AppShell />}>
          <Route path="/" element={<AssistantView />} />
          <Route path="/weather" element={<WeatherView />} />
          <Route path="/sea" element={<SeaConditionsView />} />
          <Route path="/zones" element={<FishermanMode />} />
          <Route path="/fisherman" element={<FishermanMode />} />
          <Route path="/assistant" element={<AssistantView />} />
          <Route path="/safety" element={<SafetyView />} />
          <Route path="/dashboard" element={<HomeDashboard />} />
          <Route path="/fleet" element={<FleetOptimizer />} />
          <Route path="/data-sources" element={<DataSources />} />
          <Route path="/command-center" element={<CommandCenter />} />
        </Route>

        {/* Technical Showcase Presentation */}
        <Route path="/landing" element={<Landing />} />

        {/* Catch-all redirect to Home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
