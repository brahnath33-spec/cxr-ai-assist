import React, { useEffect, useState } from 'react';
import { healthApi } from './services/api';

// --- Monochrome SVG icons (medical enterprise style) ---
const IconDashboard = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="9" />
    <rect x="14" y="3" width="7" height="5" />
    <rect x="14" y="12" width="7" height="9" />
    <rect x="3" y="16" width="7" height="5" />
  </svg>
);
const IconScan = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 7V5a2 2 0 0 1 2-2h2" />
    <path d="M17 3h2a2 2 0 0 1 2 2v2" />
    <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
    <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
    <path d="M7 12h10" />
  </svg>
);
const IconFolder = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
  </svg>
);
const IconReport = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <path d="M14 2v6h6" />
    <path d="M8 13h8" />
    <path d="M8 17h5" />
  </svg>
);
const IconSettings = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);
const IconBell = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
  </svg>
);
const IconUser = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

// --- Sidebar navigation ---
function Sidebar() {
  const navItems = [
    { icon: <IconDashboard />, label: 'Dashboard', active: true },
    { icon: <IconScan />, label: 'New Study', active: false },
    { icon: <IconFolder />, label: 'Worklist', active: false },
    { icon: <IconReport />, label: 'Reports', active: false },
    { icon: <IconSettings />, label: 'Settings', active: false },
  ];

  return (
    <aside className="w-60 bg-slate-900 text-slate-300 flex flex-col fixed h-full">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-sky-600 rounded flex items-center justify-center text-white font-bold text-xs tracking-wider">
            CXR
          </div>
          <div>
            <div className="text-sm font-semibold text-white leading-tight">CXR-AI Assist</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Clinical v1.0</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <div className="px-2 mb-2 text-[10px] uppercase tracking-wider text-slate-500 font-medium">
          Clinical
        </div>
        {navItems.map((item, idx) => (
          <button
            key={idx}
            className={
              'w-full flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ' +
              (item.active
                ? 'bg-slate-800 text-white border-l-2 border-sky-500'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white border-l-2 border-transparent')
            }
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Footer info */}
      <div className="px-5 py-4 border-t border-slate-800 text-[10px] text-slate-500 space-y-1">
        <div className="flex justify-between">
          <span>Build</span>
          <span className="font-mono text-slate-400">1.0.0</span>
        </div>
        <div className="flex justify-between">
          <span>Env</span>
          <span className="font-mono text-slate-400">DEV</span>
        </div>
      </div>
    </aside>
  );
}

// --- Top bar ---
function TopBar({ apiStatus }) {
  const dotClass = 'w-1.5 h-1.5 rounded-full ' + (apiStatus ? 'bg-emerald-500' : 'bg-red-500');
  const statusText = apiStatus ? 'Connected' : 'Disconnected';
  const statusColor = apiStatus ? 'text-emerald-600' : 'text-red-600';
  const statusBg = apiStatus ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200';

  return (
    <header className="fixed top-0 left-60 right-0 h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10">
      <div className="flex items-center gap-3 text-sm">
        <span className="text-slate-400">CXR-AI Assist</span>
        <span className="text-slate-300">/</span>
        <span className="text-slate-900 font-medium">Dashboard</span>
      </div>

      <div className="flex items-center gap-4">
        <div className={'flex items-center gap-2 px-3 py-1 rounded border text-xs font-medium ' + statusBg + ' ' + statusColor}>
          <span className={dotClass}></span>
          <span>{statusText}</span>
        </div>
        <button className="text-slate-400 hover:text-slate-600">
          <IconBell />
        </button>
        <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
          <div className="w-7 h-7 rounded bg-slate-200 flex items-center justify-center text-slate-600">
            <IconUser />
          </div>
          <div className="text-xs">
            <div className="font-medium text-slate-900">Radiologist</div>
            <div className="text-slate-500">admin@cxrai.local</div>
          </div>
        </div>
      </div>
    </header>
  );
}

// --- Main dashboard content ---
function Dashboard({ health, error }) {
  const systemRows = health
    ? [
        { label: 'Service Status', value: health.status.toUpperCase(), mono: true, accent: 'text-emerald-600' },
        { label: 'Application', value: health.app_name, mono: false },
        { label: 'Version', value: health.version, mono: true },
        { label: 'Environment', value: health.environment.toUpperCase(), mono: true },
        { label: 'Uptime', value: Math.floor(health.uptime_seconds) + ' s', mono: true },
        { label: 'Endpoint', value: 'localhost:8000/api/v1', mono: true },
      ]
    : [];

  const capabilities = [
    { code: 'CXR-MPD-01', name: 'Multi-Pathology Detection', status: 'Ready', coverage: '5 conditions' },
    { code: 'CXR-CTR-02', name: 'Cardiothoracic Ratio', status: 'Ready', coverage: 'Automated' },
    { code: 'CXR-GCM-03', name: 'Grad-CAM Explainability', status: 'Ready', coverage: 'Per-prediction' },
    { code: 'CXR-RPT-04', name: 'Draft Report Generation', status: 'Pending', coverage: 'Structured text' },
    { code: 'CXR-DCM-05', name: 'DICOM Ingestion', status: 'Pending', coverage: 'PACS-compatible' },
  ];

  const statusPill = (status) => {
    if (status === 'Ready') {
      return 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase tracking-wide';
    }
    return 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wide';
  };

  return (
    <main className="ml-60 mt-14 p-6 bg-slate-50 min-h-screen">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">System Dashboard</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Clinical decision support platform &middot; Chest radiograph analysis module
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-5 flex items-start gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded">
          <div className="w-1 h-full bg-red-500 rounded-full -ml-1 mt-0.5" style={{height: 'auto', alignSelf: 'stretch'}}></div>
          <div className="flex-1">
            <div className="text-sm font-medium text-red-800">Backend Connection Failed</div>
            <div className="text-xs text-red-600 mt-0.5 font-mono">{error}</div>
          </div>
        </div>
      )}

      {/* Metrics grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Studies Processed', value: '0', sub: 'today', mono: true },
          { label: 'Avg. Inference Time', value: '—', sub: 'ms per scan', mono: true },
          { label: 'Model AUC', value: '—', sub: 'validation', mono: true },
          { label: 'Active Sessions', value: '1', sub: 'current user', mono: true },
        ].map((m, i) => (
          <div key={i} className="bg-white border border-slate-200 rounded p-4">
            <div className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
              {m.label}
            </div>
            <div className="mt-2 text-2xl font-semibold text-slate-900 font-mono">
              {m.value}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-3 gap-4">
        {/* System status panel (wider) */}
        <div className="col-span-2 bg-white border border-slate-200 rounded">
          <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">System Information</h2>
            <span className="text-[10px] font-mono text-slate-400">GET /api/v1/health</span>
          </div>
          {health ? (
            <div className="divide-y divide-slate-100">
              {systemRows.map((row, i) => (
                <div key={i} className="flex items-center justify-between px-5 py-2.5">
                  <span className="text-xs text-slate-500">{row.label}</span>
                  <span className={
                    'text-xs ' +
                    (row.mono ? 'font-mono ' : 'font-medium ') +
                    (row.accent || 'text-slate-800')
                  }>
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="px-5 py-10 text-center text-xs text-slate-400">
              {error ? 'Unable to reach backend service.' : 'Loading system information...'}
            </div>
          )}
        </div>

        {/* Capabilities panel */}
        <div className="bg-white border border-slate-200 rounded">
          <div className="px-5 py-3 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-slate-900">Platform Modules</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {capabilities.map((cap, i) => (
              <div key={i} className="px-5 py-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono text-slate-400">{cap.code}</span>
                  <span className={statusPill(cap.status)}>{cap.status}</span>
                </div>
                <div className="text-xs font-medium text-slate-800">{cap.name}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{cap.coverage}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer note */}
      <div className="mt-6 flex items-center justify-between text-[10px] text-slate-400 font-mono">
        <div>SESSION: LOCAL-DEV &middot; USER: admin@cxrai.local</div>
        <div>FOR INVESTIGATIONAL USE ONLY &middot; NOT FOR PRIMARY DIAGNOSIS</div>
      </div>
    </main>
  );
}

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    healthApi.check()
      .then((res) => setHealth(res.data))
      .catch((err) => setError(err.message || 'Network Error'));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <TopBar apiStatus={!!health} />
      <Dashboard health={health} error={error} />
    </div>
  );
}

export default App;
