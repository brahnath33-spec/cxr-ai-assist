import React, { useEffect, useState, useRef } from 'react';
import { healthApi, predictionApi } from './services/api';

const IconDashboard = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" /><rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" /></svg>);
const IconScan = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" /><path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" /><path d="M7 12h10" /></svg>);
const IconFolder = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" /></svg>);
const IconReport = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /><path d="M8 13h8" /><path d="M8 17h5" /></svg>);
const IconSettings = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>);
const IconBell = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>);
const IconUser = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>);
const IconUpload = () => (<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>);
const IconFile = () => (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /></svg>);

function Sidebar({ currentPage, onNavigate }) {
  const navItems = [
    { id: 'dashboard', icon: <IconDashboard />, label: 'Dashboard' },
    { id: 'new-study', icon: <IconScan />, label: 'New Study' },
    { id: 'worklist', icon: <IconFolder />, label: 'Worklist', disabled: true },
    { id: 'reports', icon: <IconReport />, label: 'Reports', disabled: true },
    { id: 'settings', icon: <IconSettings />, label: 'Settings', disabled: true },
  ];
  return (
    <aside className="w-60 bg-slate-900 text-slate-300 flex flex-col fixed h-full">
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-sky-600 rounded flex items-center justify-center text-white font-bold text-xs tracking-wider">CXR</div>
          <div>
            <div className="text-sm font-semibold text-white leading-tight">CXR-AI Assist</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Clinical v1.0</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <div className="px-2 mb-2 text-[10px] uppercase tracking-wider text-slate-500 font-medium">Clinical</div>
        {navItems.map((item) => (
          <button key={item.id} onClick={() => !item.disabled && onNavigate(item.id)} disabled={item.disabled}
            className={'w-full flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ' + (item.disabled ? 'text-slate-600 cursor-not-allowed ' : (currentPage === item.id ? 'bg-slate-800 text-white border-l-2 border-sky-500' : 'text-slate-400 hover:bg-slate-800 hover:text-white border-l-2 border-transparent'))}>
            {item.icon}<span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="px-5 py-4 border-t border-slate-800 text-[10px] text-slate-500 space-y-1">
        <div className="flex justify-between"><span>Build</span><span className="font-mono text-slate-400">1.0.0</span></div>
        <div className="flex justify-between"><span>Env</span><span className="font-mono text-slate-400">DEV</span></div>
      </div>
    </aside>
  );
}

function TopBar({ apiStatus, currentPage }) {
  const dotClass = 'w-1.5 h-1.5 rounded-full ' + (apiStatus ? 'bg-emerald-500' : 'bg-red-500');
  const statusText = apiStatus ? 'Connected' : 'Disconnected';
  const statusColor = apiStatus ? 'text-emerald-600' : 'text-red-600';
  const statusBg = apiStatus ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200';
  const pageLabel = currentPage === 'new-study' ? 'New Study' : currentPage === 'dashboard' ? 'Dashboard' : 'Worklist';
  return (
    <header className="fixed top-0 left-60 right-0 h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10">
      <div className="flex items-center gap-3 text-sm">
        <span className="text-slate-400">CXR-AI Assist</span>
        <span className="text-slate-300">/</span>
        <span className="text-slate-900 font-medium">{pageLabel}</span>
      </div>
      <div className="flex items-center gap-4">
        <div className={'flex items-center gap-2 px-3 py-1 rounded border text-xs font-medium ' + statusBg + ' ' + statusColor}>
          <span className={dotClass}></span><span>{statusText}</span>
        </div>
        <button className="text-slate-400 hover:text-slate-600"><IconBell /></button>
        <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
          <div className="w-7 h-7 rounded bg-slate-200 flex items-center justify-center text-slate-600"><IconUser /></div>
          <div className="text-xs">
            <div className="font-medium text-slate-900">Radiologist</div>
            <div className="text-slate-500">admin@cxrai.local</div>
          </div>
        </div>
      </div>
    </header>
  );
}

function Dashboard({ health, error }) {
  const systemRows = health ? [
    { label: 'Service Status', value: health.status.toUpperCase(), mono: true, accent: 'text-emerald-600' },
    { label: 'Application', value: health.app_name, mono: false },
    { label: 'Version', value: health.version, mono: true },
    { label: 'Environment', value: health.environment.toUpperCase(), mono: true },
    { label: 'Uptime', value: Math.floor(health.uptime_seconds) + ' s', mono: true },
    { label: 'Endpoint', value: 'localhost:8000/api/v1', mono: true },
  ] : [];
  const capabilities = [
    { code: 'CXR-MPD-01', name: 'Multi-Pathology Detection', status: 'Ready', coverage: '5 conditions' },
    { code: 'CXR-CTR-02', name: 'Cardiothoracic Ratio', status: 'Ready', coverage: 'Automated' },
    { code: 'CXR-GCM-03', name: 'Grad-CAM Explainability', status: 'Ready', coverage: 'Per-prediction' },
    { code: 'CXR-RPT-04', name: 'Draft Report Generation', status: 'Pending', coverage: 'Structured text' },
    { code: 'CXR-DCM-05', name: 'DICOM Ingestion', status: 'Pending', coverage: 'PACS-compatible' },
  ];
  const statusPill = (status) => status === 'Ready' ? 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase tracking-wide' : 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wide';
  return (
    <main className="ml-60 mt-14 p-6 bg-slate-50 min-h-screen">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">System Dashboard</h1>
        <p className="text-xs text-slate-500 mt-0.5">Clinical decision support platform &middot; Chest radiograph analysis module</p>
      </div>
      {error && (<div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 rounded"><div className="text-sm font-medium text-red-800">Backend Connection Failed</div><div className="text-xs text-red-600 mt-0.5 font-mono">{error}</div></div>)}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[{ label: 'Studies Processed', value: '0', sub: 'today' }, { label: 'Avg. Inference Time', value: '63', sub: 'ms per scan' }, { label: 'Model AUC', value: '0.62', sub: 'validation' }, { label: 'Active Sessions', value: '1', sub: 'current user' }].map((m, i) => (
          <div key={i} className="bg-white border border-slate-200 rounded p-4">
            <div className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">{m.label}</div>
            <div className="mt-2 text-2xl font-semibold text-slate-900 font-mono">{m.value}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-white border border-slate-200 rounded">
          <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between"><h2 className="text-sm font-semibold text-slate-900">System Information</h2><span className="text-[10px] font-mono text-slate-400">GET /api/v1/health</span></div>
          {health ? (
            <div className="divide-y divide-slate-100">
              {systemRows.map((row, i) => (
                <div key={i} className="flex items-center justify-between px-5 py-2.5">
                  <span className="text-xs text-slate-500">{row.label}</span>
                  <span className={'text-xs ' + (row.mono ? 'font-mono ' : 'font-medium ') + (row.accent || 'text-slate-800')}>{row.value}</span>
                </div>
              ))}
            </div>
          ) : (<div className="px-5 py-10 text-center text-xs text-slate-400">{error ? 'Unable to reach backend service.' : 'Loading system information...'}</div>)}
        </div>
        <div className="bg-white border border-slate-200 rounded">
          <div className="px-5 py-3 border-b border-slate-200"><h2 className="text-sm font-semibold text-slate-900">Platform Modules</h2></div>
          <div className="divide-y divide-slate-100">
            {capabilities.map((cap, i) => (
              <div key={i} className="px-5 py-3">
                <div className="flex items-center justify-between mb-1"><span className="text-[10px] font-mono text-slate-400">{cap.code}</span><span className={statusPill(cap.status)}>{cap.status}</span></div>
                <div className="text-xs font-medium text-slate-800">{cap.name}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{cap.coverage}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-6 flex items-center justify-between text-[10px] text-slate-400 font-mono">
        <div>SESSION: LOCAL-DEV &middot; USER: admin@cxrai.local</div>
        <div>FOR INVESTIGATIONAL USE ONLY &middot; NOT FOR PRIMARY DIAGNOSIS</div>
      </div>
    </main>
  );
}

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

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;
    if (!selectedFile.type.startsWith('image/')) { setError('Please upload a JPEG or PNG chest X-ray.'); return; }
    setFile(selectedFile); setResult(null); setExplainResult(null); setShowHeatmap(false); setError(null);
    setPreview(URL.createObjectURL(selectedFile));
  };
  const handleDrop = (e) => { e.preventDefault(); if (e.dataTransfer.files && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); };
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

  const pathologyOrder = ['Cardiomegaly', 'Pleural Effusion', 'Consolidation', 'Atelectasis', 'Pneumothorax'];
  const displayImage = showHeatmap && explainResult && explainResult.heatmap ? explainResult.heatmap : preview;

  return (
    <main className="ml-60 mt-14 p-6 bg-slate-50 min-h-screen">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">New Study</h1>
        <p className="text-xs text-slate-500 mt-0.5">Upload a chest radiograph for AI-assisted analysis</p>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded">
          <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">Input Image</h2>
            <span className="text-[10px] font-mono text-slate-400">POST /api/v1/predict/</span>
          </div>
          <div className="p-5">
            {!preview ? (
              <div onClick={() => inputRef.current && inputRef.current.click()} onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}
                className="border-2 border-dashed border-slate-300 rounded-lg py-16 flex flex-col items-center justify-center cursor-pointer hover:border-sky-500 hover:bg-sky-50/30 transition-colors">
                <div className="text-slate-400 mb-3"><IconUpload /></div>
                <div className="text-sm font-medium text-slate-700">Drop chest X-ray here</div>
                <div className="text-xs text-slate-500 mt-1">or click to browse &middot; JPEG / PNG</div>
                <input ref={inputRef} type="file" accept="image/jpeg,image/jpg,image/png,image/webp" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
              </div>
            ) : (
              <div>
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-900 relative">
                  <img src={displayImage} alt="Chest X-ray" className="w-full h-auto max-h-96 object-contain" />
                  {showHeatmap && (<div className="absolute top-2 left-2 px-2 py-1 bg-rose-600/90 text-white text-[10px] font-medium rounded uppercase tracking-wider">Grad-CAM Active</div>)}
                </div>
                {explainResult && explainResult.heatmap && (
                  <div className="mt-3 flex items-center gap-2">
                    <button onClick={() => setShowHeatmap(!showHeatmap)} className="text-xs px-3 py-1.5 border border-slate-300 rounded text-slate-600 hover:bg-slate-50">
                      {showHeatmap ? 'Show Original' : 'Show Heatmap'}
                    </button>
                    <span className="text-[10px] text-slate-500">Explaining: <span className="font-mono">{explainResult.target_label}</span></span>
                  </div>
                )}
                <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                  <IconFile /><span className="font-mono truncate">{file.name}</span>
                  <span className="text-slate-400">&middot; {(file.size / 1024).toFixed(0)} KB</span>
                </div>
                <div className="mt-4 flex gap-2">
                  <button onClick={handlePredict} disabled={loading} className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed">{loading ? 'Analyzing...' : 'Run AI Analysis'}</button>
                  <button onClick={handleReset} className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50">Clear</button>
                </div>
              </div>
            )}
            {error && (<div className="mt-4 px-4 py-3 bg-red-50 border border-red-200 rounded text-sm text-red-700"><strong className="font-medium">Error:</strong> {error}</div>)}
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded">
          <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">AI Analysis</h2>
            {result && <span className="text-[10px] font-mono text-slate-400">{result.inference_time_ms} ms</span>}
          </div>
          <div className="p-5">
            {!result && !loading && (<div className="py-16 text-center text-xs text-slate-400">{preview ? 'Click "Run AI Analysis" to begin' : 'Upload an image to begin analysis'}</div>)}
            {loading && (<div className="py-16 text-center"><div className="inline-block w-6 h-6 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div><div className="mt-3 text-xs text-slate-500">Running inference...</div></div>)}
            {result && (
              <div className="space-y-4">
                <div className={'px-4 py-3 rounded border text-sm font-medium ' + (result.flagged.length > 0 ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800')}>
                  {result.flagged.length > 0 ? result.flagged.length + ' pathology finding(s) flagged for review' : 'No pathologies flagged above clinical threshold'}
                </div>
                <div className="border border-slate-200 rounded divide-y divide-slate-100">
                  {pathologyOrder.map((label) => {
                    const prob = result.predictions[label] || 0;
                    const pct = (prob * 100).toFixed(1);
                    const isFlagged = prob >= 0.5;
                    const barColor = isFlagged ? 'bg-amber-500' : prob >= 0.3 ? 'bg-sky-400' : 'bg-slate-300';
                    return (
                      <div key={label} className="px-4 py-3">
                        <div className="flex items-center justify-between mb-2"><span className="text-xs font-medium text-slate-800">{label}</span><span className={'text-xs font-mono ' + (isFlagged ? 'text-amber-700 font-semibold' : 'text-slate-600')}>{pct}%</span></div>
                        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden"><div className={'h-full ' + barColor + ' transition-all duration-500'} style={{ width: pct + '%' }}></div></div>
                      </div>
                    );
                  })}
                </div>
                <div className="border border-sky-200 bg-sky-50/50 rounded p-4">
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-slate-900">AI Reasoning (Grad-CAM)</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">See which regions the model focused on</div>
                  </div>
                  <div className="flex gap-2">
                    <select value={targetLabel} onChange={(e) => setTargetLabel(e.target.value)} className="flex-1 text-xs px-3 py-2 border border-slate-300 rounded bg-white">
                      <option value="">Auto (highest confidence)</option>
                      {pathologyOrder.map((label) => (<option key={label} value={label}>{label}</option>))}
                    </select>
                    <button onClick={handleExplain} disabled={explaining} className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-medium rounded transition-colors disabled:opacity-50">{explaining ? 'Generating...' : 'Explain'}</button>
                  </div>
                </div>
                <div className="text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-100 space-y-1">
                  <div className="flex justify-between"><span>MODEL</span><span>{result.model_version}</span></div>
                  <div className="flex justify-between"><span>INFERENCE</span><span>{result.inference_time_ms} ms</span></div>
                  <div className="flex justify-between"><span>DIMENSIONS</span><span>{result.image_dimensions[0]} × {result.image_dimensions[1]}</span></div>
                  <div className="flex justify-between"><span>CONFIDENCE</span><span>{(result.confidence * 100).toFixed(1)}%</span></div>
                </div>
                <div className="text-[10px] text-slate-400 text-center pt-2">For investigational use only &middot; Not for primary diagnosis</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { healthApi.check().then((res) => setHealth(res.data)).catch((err) => setError(err.message || 'Network Error')); }, []);
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <TopBar apiStatus={!!health} currentPage={currentPage} />
      {currentPage === 'dashboard' && <Dashboard health={health} error={error} />}
      {currentPage === 'new-study' && <NewStudy />}
    </div>
  );
}

export default App;