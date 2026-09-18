import ReportsPage from './pages/ReportsPage';
import React, { useEffect, useState, useRef } from 'react';
import { healthApi, predictionApi } from './services/api';

// ============ ICONS ============
const I = {
  Dashboard: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>,
  Scan: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/></svg>,
  Folder: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/></svg>,
  Report: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h5"/></svg>,
  Settings: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  Bell: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>,
  User: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
  Upload: () => <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
  File: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>,
  Eye: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>,
  Sparkles: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>,
  Alert: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>,
  Check: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  Activity: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>,
  Clock: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
  Trending: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>,
};

// ============ SIDEBAR ============
function Sidebar({ currentPage, onNavigate }) {
  const items = [
    { id: 'dashboard', icon: <I.Dashboard />, label: 'Dashboard' },
    { id: 'new-study', icon: <I.Scan />, label: 'New Study' },
    { id: 'reports', icon: <I.Report />, label: 'Reports' },
  ];
  return (
    <aside className="w-64 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 text-slate-300 flex flex-col fixed h-full shadow-2xl">
      <div className="px-5 py-6 border-b border-slate-800/60">
  <div className="flex items-center gap-3">
    <img src="/assets/mark.svg" alt="Navantix Pulmo" width="40" height="40" className="flex-shrink-0" />
    <div className="min-w-0">
      <div className="text-[13px] font-extrabold text-white leading-tight tracking-tight">
        NAVANTIX
      </div>
      <div className="text-[13px] font-extrabold leading-tight tracking-tight text-sky-400 -mt-0.5">
        PULMO
      </div>
      <div className="flex items-center gap-1 mt-1.5">
        <div className="w-2.5 h-[1.5px] bg-cyan-400 rounded-full"></div>
        <div className="text-[9px] text-slate-500 uppercase tracking-widest font-semibold">Clinical v1.0</div>
      </div>
    </div>
  </div>
</div>      <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
        <div className="px-3 mb-3 text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Clinical</div>
        {items.map((item) => (
          <button key={item.id} onClick={() => !item.disabled && onNavigate(item.id)} disabled={item.disabled}
            className={
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ' +
              (item.disabled
                ? 'text-slate-600 cursor-not-allowed '
                : (currentPage === item.id
                    ? 'bg-gradient-to-r from-sky-500/20 to-sky-500/5 text-white border border-sky-500/30 shadow-lg shadow-sky-500/10'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'))
            }>
            <span className={currentPage === item.id ? 'text-sky-400' : ''}>{item.icon}</span>
            <span>{item.label}</span>
            {currentPage === item.id && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-sky-400 shadow-lg shadow-sky-400/50 animate-pulse-slow"></span>}
          </button>
        ))}
      </nav>
      <div className="px-5 py-4 border-t border-slate-800/60 space-y-2">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-slate-500 uppercase tracking-wider font-semibold">Version</span>
          <span className="font-mono text-slate-400">1.0.0</span>
        </div>
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-slate-500 uppercase tracking-wider font-semibold">Status</span>
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-slow"></span>
            <span className="font-mono">LIVE</span>
          </span>
        </div>
      </div>
    </aside>
  );
}

// ============ TOPBAR ============
function TopBar({ apiStatus, currentPage }) {
  const label = { 'dashboard': 'Dashboard', 'new-study': 'New Study' }[currentPage] || 'Reports';
  return (
    <header className="fixed top-0 left-64 right-0 h-16 glass border-b border-slate-200/80 flex items-center justify-between px-8 z-10 shadow-sm">
      <div className="flex items-center gap-3 text-sm">
        <span className="text-slate-400 font-medium">Navantix Pulmo</span>
        <span className="text-slate-300">/</span>
        <span className="text-slate-900 font-semibold">{label}</span>
      </div>
      <div className="flex items-center gap-3">
        <div className={
          'flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold transition-all duration-300 ' +
          (apiStatus
            ? 'bg-emerald-50/80 border-emerald-200 text-emerald-700'
            : 'bg-red-50/80 border-red-200 text-red-700')
        }>
          <span className={'w-1.5 h-1.5 rounded-full ' + (apiStatus ? 'bg-emerald-500 animate-pulse-slow' : 'bg-red-500')}></span>
          <span>{apiStatus ? 'Connected' : 'Disconnected'}</span>
        </div>
        <button className="w-9 h-9 flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors relative">
          <I.Bell />
          <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-rose-500"></span>
        </button>
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center text-white">
            <I.User />
          </div>
          <div className="text-xs leading-tight">
            <div className="font-semibold text-slate-900">Radiologist</div>
            <div className="text-slate-500 text-[10px]">admin@navantixpulmo.local</div>
          </div>
        </div>
      </div>
    </header>
  );
}

// ============ DASHBOARD ============
function Dashboard({ health, error }) {
  const stats = [
    { label: 'Studies Today', value: 0, icon: <I.Activity />, sub: 'last 24 hours', color: 'sky' },
    { label: 'Avg. Inference', value: '82', icon: <I.Clock />, sub: 'milliseconds', color: 'violet', suffix: 'ms' },
    { label: 'Model AUC', value: '0.62', icon: <I.Trending />, sub: 'validation set', color: 'emerald' },
    { label: 'Active Sessions', value: 1, icon: <I.User />, sub: 'current user', color: 'amber' },
  ];
  const capabilities = [
    { code: 'CXR-MPD-01', name: 'Multi-Pathology Detection', status: 'Ready', coverage: '5 conditions' },
    { code: 'CXR-CTR-02', name: 'Cardiothoracic Ratio', status: 'Ready', coverage: 'Automated' },
    { code: 'CXR-GCM-03', name: 'Grad-CAM Explainability', status: 'Ready', coverage: 'Per-prediction' },
    { code: 'CXR-RPT-04', name: 'Draft Report Generation', status: 'Ready', coverage: 'Structured text' },
    { code: 'CXR-DCM-05', name: 'DICOM Ingestion', status: 'Ready', coverage: 'PACS-compatible' },
  ];
  const colorMap = {
    sky: 'from-sky-500 to-sky-600 shadow-sky-500/30',
    violet: 'from-violet-500 to-violet-600 shadow-violet-500/30',
    emerald: 'from-emerald-500 to-emerald-600 shadow-emerald-500/30',
    amber: 'from-amber-500 to-amber-600 shadow-amber-500/30',
  };
  return (
    <main className="ml-64 mt-16 p-8 bg-slate-50 min-h-screen">
      <div className="mb-8 animate-slide-up">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Clinical decision support platform &middot; Chest radiograph analysis</p>
      </div>
      {error && (
        <div className="mb-6 flex items-start gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-xl animate-slide-up">
          <span className="text-red-500 mt-0.5"><I.Alert /></span>
          <div className="flex-1">
            <div className="text-sm font-semibold text-red-800">Backend Connection Failed</div>
            <div className="text-xs text-red-600 mt-0.5 font-mono">{error}</div>
          </div>
        </div>
      )}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map((s, i) => (
          <div key={i} className="stat-card animate-slide-up" style={{ animationDelay: (i * 60) + 'ms' }}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">{s.label}</span>
              <div className={'w-8 h-8 rounded-lg bg-gradient-to-br ' + colorMap[s.color] + ' flex items-center justify-center text-white shadow-lg'}>
                {s.icon}
              </div>
            </div>
            <div className="text-3xl font-bold text-slate-900 font-mono tracking-tight">
              {s.value}{s.suffix && <span className="text-lg text-slate-400 ml-0.5">{s.suffix}</span>}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">{s.sub}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 card animate-slide-up" style={{ animationDelay: '240ms' }}>
          <div className="card-header">
            <h2 className="text-sm font-bold text-slate-900">System Information</h2>
            <span className="text-[10px] font-mono text-slate-400 bg-slate-50 px-2 py-1 rounded">GET /api/v1/health</span>
          </div>
          {health ? (
            <div className="divide-y divide-slate-100">
              {[
                { label: 'Service Status', value: health.status.toUpperCase(), mono: true, accent: 'text-emerald-600', dot: true },
                { label: 'Application', value: health.app_name, mono: false },
                { label: 'Version', value: health.version, mono: true },
                { label: 'Environment', value: health.environment.toUpperCase(), mono: true },
                { label: 'Uptime', value: Math.floor(health.uptime_seconds) + ' seconds', mono: true },
                { label: 'API Endpoint', value: 'localhost:8000/api/v1', mono: true },
              ].map((row, i) => (
                <div key={i} className="flex items-center justify-between px-6 py-3 hover:bg-slate-50/50 transition-colors">
                  <span className="text-sm text-slate-500">{row.label}</span>
                  <span className={'text-sm flex items-center gap-2 ' + (row.mono ? 'font-mono ' : 'font-medium ') + (row.accent || 'text-slate-800')}>
                    {row.dot && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse-slow"></span>}
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="px-6 py-16 text-center text-sm text-slate-400">Loading system information...</div>
          )}
        </div>
        <div className="card animate-slide-up" style={{ animationDelay: '300ms' }}>
          <div className="card-header">
            <h2 className="text-sm font-bold text-slate-900">Platform Modules</h2>
            <span className="text-[10px] text-slate-400 font-mono">{capabilities.filter(c => c.status === 'Ready').length}/{capabilities.length}</span>
          </div>
          <div className="divide-y divide-slate-100">
            {capabilities.map((cap, i) => (
              <div key={i} className="px-5 py-3.5 hover:bg-slate-50/50 transition-colors">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono text-slate-400">{cap.code}</span>
                  <span className={'pill ' + (cap.status === 'Ready' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200')}>
                    {cap.status === 'Ready' ? <I.Check /> : <I.Clock />}
                    {cap.status}
                  </span>
                </div>
                <div className="text-xs font-semibold text-slate-800">{cap.name}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{cap.coverage}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-8 flex items-center justify-between text-[10px] text-slate-400 font-mono">
        <div>SESSION: LOCAL-DEV &middot; USER: admin@navantixpulmo.local</div>
        <div>FOR INVESTIGATIONAL USE ONLY &middot; NOT FOR PRIMARY DIAGNOSIS</div>
      </div>
    </main>
  );
}

// ============ NEW STUDY ============
function NewStudy() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [explainResult, setExplainResult] = useState(null);
  const [explaining, setExplaining] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [targetLabel, setTargetLabel] = useState('');
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const isDicomFile = (f) => {
    if (!f) return false;
    if (f.name && f.name.toLowerCase().endsWith('.dcm')) return true;
    if (f.type === 'application/dicom') return true;
    if (f.type === 'application/octet-stream' && f.name && f.name.toLowerCase().endsWith('.dcm')) return true;
    return false;
  };
  const handleFile = (f) => {
    if (!f) return;
    const isImage = f.type && f.type.startsWith('image/');
    const isDcm = isDicomFile(f);
    if (!isImage && !isDcm) {
      setError('Please upload a JPEG, PNG, or DICOM (.dcm) file.');
      return;
    }
    setFile(f); setResult(null); setExplainResult(null); setShowHeatmap(false); setError(null);
    // DICOM can't be previewed in browser - show placeholder
    if (isDcm) {
      setPreview('dicom');
    } else {
      setPreview(URL.createObjectURL(f));
    }
  };
  const handleDrop = (e) => { e.preventDefault(); if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]); };
  const handlePredict = async () => {
    if (!file) return;
    setLoading(true); setError(null); setResult(null); setExplainResult(null); setShowHeatmap(false);
    try { const res = await predictionApi.predict(file); setResult(res.data); }
    catch (err) { setError(err.response?.data?.detail || err.message || 'Prediction failed'); }
    finally { setLoading(false); }
  };
  const handleExplain = async () => {
    if (!file) return;
    setExplaining(true); setError(null);
    try { const res = await predictionApi.explain(file, targetLabel || null); setExplainResult(res.data); setShowHeatmap(true); }
    catch (err) { setError(err.response?.data?.detail || err.message || 'Explanation failed'); }
    finally { setExplaining(false); }
  };
  const handleReset = () => { setFile(null); setPreview(null); setResult(null); setExplainResult(null); setShowHeatmap(false); setTargetLabel(''); setError(null); };

  const order = ['Tuberculosis', 'Pneumonia', 'Cardiomegaly', 'Pleural Effusion', 'Consolidation', 'Atelectasis', 'Pneumothorax', 'No TB/Pneumonia'];
  const displayImage = showHeatmap && explainResult?.heatmap ? explainResult.heatmap : preview;

  const severityFor = (p, label) => {
    // Special case: 'No TB/Pneumonia' high = GOOD NEWS = green
    if (label === 'No TB/Pneumonia') {
      if (p >= 0.5) return { color: 'from-emerald-500 to-emerald-600', label: 'CLEAR', text: 'text-emerald-700' };
      return { color: 'from-amber-400 to-amber-500', label: 'UNCERTAIN', text: 'text-amber-700' };
    }
    if (p >= 0.5) return { color: 'from-amber-500 to-orange-500', label: 'Elevated', text: 'text-amber-700' };
    if (p >= 0.3) return { color: 'from-sky-400 to-sky-500', label: 'Moderate', text: 'text-sky-700' };
    return { color: 'from-slate-300 to-slate-400', label: 'Low', text: 'text-slate-600' };
  };

  return (
    <main className="ml-64 mt-16 p-8 bg-slate-50 min-h-screen">
      <div className="mb-8 animate-slide-up">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">New Study</h1>
        <p className="text-sm text-slate-500 mt-1">Upload a chest radiograph for AI-assisted analysis</p>
      </div>
      <div className="grid grid-cols-2 gap-6">
        {/* LEFT */}
        <div className="card animate-slide-up" style={{ animationDelay: '60ms' }}>
          <div className="card-header">
            <h2 className="text-sm font-bold text-slate-900">Input Image</h2>
            <span className="text-[10px] font-mono text-slate-400 bg-slate-50 px-2 py-1 rounded">POST /predict</span>
          </div>
          <div className="p-6">
            {!preview ? (
  <div onClick={() => inputRef.current?.click()} onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}
    className="border-2 border-dashed border-slate-300 rounded-xl py-20 flex flex-col items-center justify-center cursor-pointer hover:border-sky-500 hover:bg-gradient-to-b hover:from-sky-50/50 hover:to-white transition-all duration-300 group">
    <div className="text-slate-300 group-hover:text-sky-500 group-hover:scale-110 transition-all duration-300 mb-4"><I.Upload /></div>
    <div className="text-base font-semibold text-slate-700 group-hover:text-sky-700">Drop chest X-ray here</div>
    <div className="text-xs text-slate-500 mt-1">or click to browse &middot; JPEG / PNG / DICOM</div>
    <input ref={inputRef} type="file" accept="image/jpeg,image/jpg,image/png,image/webp,.dcm,application/dicom" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
  </div>
) : (
              <div className="animate-fade-in">
               <div className="relative rounded-xl overflow-hidden bg-slate-900 border border-slate-200 shadow-lg">
  {preview === 'dicom' && !showHeatmap ? (
    <div className="flex flex-col items-center justify-center py-20 text-slate-400">
      <I.File />
      <div className="mt-3 text-sm">DICOM file loaded</div>
      <div className="text-xs mt-1 text-slate-500">Click "Run AI Analysis" to process</div>
    </div>
  ) : (
    <img src={displayImage} alt="Chest X-ray" className="w-full h-auto max-h-[28rem] object-contain transition-opacity duration-500" />
  )}                  {showHeatmap && (
                    <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-rose-500 to-rose-600 text-white text-[11px] font-bold rounded-full shadow-lg shadow-rose-500/30">
                      <I.Sparkles />
                      <span className="tracking-wide">GRAD-CAM ACTIVE</span>
                    </div>
                  )}
                  <div className="absolute bottom-3 right-3 flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/80 backdrop-blur text-white text-[10px] font-mono rounded">
                    {result?.inference_time_ms} ms
                  </div>
                </div>
                {explainResult?.heatmap && (
                  <div className="mt-4 flex items-center gap-3">
                    <button onClick={() => setShowHeatmap(!showHeatmap)}
                      className={'flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ' +
                        (showHeatmap ? 'bg-sky-100 text-sky-700 border border-sky-200' : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50')}>
                      <I.Eye />
                      {showHeatmap ? 'Show Original' : 'Show Heatmap'}
                    </button>
                    <span className="text-[11px] text-slate-500">Explaining: <span className="font-mono font-semibold text-slate-700">{explainResult.target_label}</span></span>
                  </div>
                )}
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-500 bg-slate-50 px-3 py-2 rounded-lg">
                  <I.File />
                  <span className="font-mono truncate flex-1">{file.name}</span>
                  <span className="text-slate-400">&middot;</span>
                  <span className="text-slate-400">{(file.size / 1024).toFixed(0)} KB</span>
                </div>
                <div className="mt-4 flex gap-3">
                  <button onClick={handlePredict} disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2">
                    {loading ? (
                      <>
                        <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        Analyzing...
                      </>
                    ) : (<><I.Sparkles /> Run AI Analysis</>)}
                  </button>
                  <button onClick={handleReset} className="btn-secondary">Clear</button>
                </div>
              </div>
            )}
            {error && (
  <div className="mt-4 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl overflow-hidden animate-slide-up">
    <div className="flex items-center gap-3 px-4 py-3 border-b border-amber-200/70 bg-amber-100/50">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-white shadow-md shadow-amber-500/20 flex-shrink-0">
        <I.Alert />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-bold text-amber-900">Input Verification Failed</div>
        <div className="text-[11px] text-amber-700 mt-0.5">Study cannot be processed for analysis</div>
      </div>
      <span className="text-[9px] font-mono uppercase tracking-widest text-amber-600 bg-amber-200/50 px-2 py-0.5 rounded">
        CXR-VAL-01
      </span>
    </div>
    <div className="px-4 py-3">
      <p className="text-sm text-amber-900 leading-relaxed">{error}</p>
    </div>
    <div className="px-4 py-2 border-t border-amber-200/70 bg-white/40 flex items-start gap-2">
      <div className="text-[10px] text-amber-700 leading-relaxed">
        <span className="font-semibold">Reference:</span> Navantix Pulmo accepts PA/AP chest radiographs
        in diagnostic grayscale (CR, DX, DR). Verify the study is a radiographic chest projection
        and resubmit.
      </div>
    </div>
  </div>
)}          </div>
        </div>

        {/* RIGHT */}
        <div className="card animate-slide-up" style={{ animationDelay: '120ms' }}>
          <div className="card-header">
            <h2 className="text-sm font-bold text-slate-900">AI Analysis</h2>
            {result && (
              <span className="text-[10px] font-mono text-slate-400 bg-slate-50 px-2 py-1 rounded flex items-center gap-1.5">
                <I.Clock /> {result.inference_time_ms} ms
              </span>
            )}
          </div>
          <div className="p-6">
            {!result && !loading && (
              <div className="py-24 text-center">
                <div className="text-slate-300 mb-3 flex justify-center"><I.Scan /></div>
                <div className="text-sm text-slate-400">{preview ? 'Click "Run AI Analysis" to begin' : 'Upload an image to begin analysis'}</div>
              </div>
            )}
            {loading && (
              <div className="py-24 text-center animate-fade-in">
                <div className="inline-flex flex-col items-center gap-4">
                  <div className="relative">
                    <div className="w-12 h-12 border-4 border-sky-100 rounded-full"></div>
                    <div className="absolute inset-0 w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                  <div className="text-xs text-slate-500 font-medium">Running inference...</div>
                </div>
              </div>
            )}
            {result && (
              <div className="space-y-5 animate-fade-in">
                <div className={
                  'flex items-center gap-3 px-4 py-3.5 rounded-xl border font-semibold text-sm ' +
                  (result.flagged.length > 0
                    ? 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200 text-amber-800'
                    : 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200 text-emerald-800')
                }>
                  <div className={
                    'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ' +
                    (result.flagged.length > 0 ? 'bg-amber-500 text-white' : 'bg-emerald-500 text-white')
                  }>
                    {result.flagged.length > 0 ? <I.Alert /> : <I.Check />}
                  </div>
                  <div className="flex-1">
                    {result.flagged.length > 0
                      ? `${result.flagged.length} patholog${result.flagged.length === 1 ? 'y' : 'ies'} flagged for review`
                      : 'No pathologies flagged above clinical threshold'}
                  </div>
                </div>
                <div className="border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100">
                  {order.map((label) => {
                    const p = result.predictions[label] || 0;
                    const pct = (p * 100).toFixed(1);
                    const sev = severityFor(p, label);
                    return (
                      <div key={label} className="px-4 py-3 hover:bg-slate-50/50 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-slate-800">{label}</span>
                          <div className="flex items-center gap-2">
                            <span className={'text-[10px] uppercase tracking-wider font-bold ' + sev.text}>{sev.label}</span>
                            <span className={'text-sm font-mono font-bold tabular-nums ' + sev.text}>{pct}%</span>
                          </div>
                        </div>
                        <div className="progress-track">
                          <div className={'progress-fill bg-gradient-to-r ' + sev.color} style={{ width: pct + '%' }}></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="border border-sky-200 bg-gradient-to-br from-sky-50 to-white rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-sky-500 to-sky-600 flex items-center justify-center text-white shadow-md shadow-sky-500/30">
                      <I.Sparkles />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-900">AI Reasoning (Grad-CAM)</div>
                      <div className="text-[10px] text-slate-500">See which regions the model focused on</div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <select value={targetLabel} onChange={(e) => setTargetLabel(e.target.value)}
                      className="flex-1 text-xs px-3 py-2.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none transition-all">
                      <option value="">Auto (highest confidence)</option>
                      {order.map((l) => (<option key={l} value={l}>{l}</option>))}
                    </select>
                    <button onClick={handleExplain} disabled={explaining}
                      className="px-5 py-2.5 bg-gradient-to-b from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white text-xs font-semibold rounded-lg shadow-md shadow-sky-500/20 hover:shadow-lg transition-all duration-200 disabled:opacity-60 flex items-center gap-2">
                      {explaining ? (<><span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>Generating</>) : (<><I.Sparkles />Explain</>)}
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100">
                  {[
                    { k: 'MODEL', v: result.model_version },
                    { k: 'DIMENSIONS', v: result.image_dimensions[0] + ' ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¾ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ' + result.image_dimensions[1] },
                    { k: 'INFERENCE', v: result.inference_time_ms + ' ms' },
                    { k: 'CONFIDENCE', v: (result.confidence * 100).toFixed(1) + '%' },
                  ].map((m, i) => (
                    <div key={i} className="bg-slate-50 rounded-lg px-3 py-2">
                      <div className="text-[9px] uppercase tracking-widest text-slate-400 font-bold">{m.k}</div>
                      <div className="text-xs font-mono text-slate-700 mt-0.5 truncate">{m.v}</div>
                    </div>
                  ))}
                </div>
                <div className="text-[10px] text-slate-400 text-center pt-1 flex items-center justify-center gap-1.5">
                  <I.Alert />
                  For investigational use only &middot; Not for primary diagnosis
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

// ============ APP ============
function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { healthApi.check().then((r) => setHealth(r.data)).catch((e) => setError(e.message || 'Network Error')); }, []);
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <TopBar apiStatus={!!health} currentPage={currentPage} />
      {currentPage === 'dashboard' && <Dashboard health={health} error={error} />}
      {currentPage === 'new-study' && <NewStudy />}
      {currentPage === 'reports' && <ReportsPage />}
    </div>
  );
}

export default App;