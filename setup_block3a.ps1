import React, { useEffect, useState } from 'react';
import { healthApi } from './services/api';

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    healthApi.check()
      .then((res) => setHealth(res.data))
      .catch((err) => setError(err.message));
  }, []);

  const dotClass = "w-2 h-2 rounded-full animate-pulse " + (health ? "bg-success-500" : "bg-warning-500");

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
              CXR
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">CXR-AI Assist</h1>
              <p className="text-xs text-gray-500">Clinical Decision Support</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={dotClass}></span>
            <span className="text-sm text-gray-600">{health ? 'API Connected' : 'Connecting...'}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Intelligent Chest X-Ray Triage
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Multi-pathology detection, automated Cardiothoracic Ratio calculation, and draft report generation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="card">
            <div className="text-primary-600 text-3xl mb-2">🎯</div>
            <h3 className="font-bold text-lg mb-1">5 Pathologies</h3>
            <p className="text-sm text-gray-600">Cardiomegaly, Effusion, Consolidation, Nodule, Pneumothorax</p>
          </div>
          <div className="card">
            <div className="text-primary-600 text-3xl mb-2">📏</div>
            <h3 className="font-bold text-lg mb-1">Auto CTR</h3>
            <p className="text-sm text-gray-600">Cardiothoracic Ratio computed in under 2 seconds</p>
          </div>
          <div className="card">
            <div className="text-primary-600 text-3xl mb-2">🔥</div>
            <h3 className="font-bold text-lg mb-1">Grad-CAM</h3>
            <p className="text-sm text-gray-600">Heatmaps show AI reasoning for clinical trust</p>
          </div>
        </div>

        <div className="card max-w-3xl mx-auto">
          <h3 className="font-bold text-lg mb-4">Backend Status</h3>
          {error && (
            <div className="bg-danger-500/10 border border-danger-500 text-danger-600 rounded-lg p-4">
              <strong>Connection Error:</strong> {error}
            </div>
          )}
          {health && (
            <div className="space-y-2 font-mono text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Status:</span><span className="text-success-600 font-bold">{health.status}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">App:</span><span>{health.app_name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Version:</span><span>{health.version}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Environment:</span><span>{health.environment}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Uptime:</span><span>{health.uptime_seconds}s</span></div>
            </div>
          )}
          {!health && !error && (
            <div className="text-gray-500 text-center py-4">Connecting to backend...</div>
          )}
        </div>
      </main>

      <footer className="text-center py-8 text-sm text-gray-500">
        CXR-AI Assist v1.0.0 &copy; 2026 &middot; Built for clinical excellence
      </footer>
    </div>
  );
}

export default App;