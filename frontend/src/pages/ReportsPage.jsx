import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const severityColor = (pct, label) => {
  if (label === 'No TB/Pneumonia') {
    return pct >= 50 ? 'text-emerald-700' : 'text-amber-700';
  }
  if (pct >= 50) return 'text-amber-700';
  if (pct >= 30) return 'text-sky-700';
  return 'text-slate-500';
};

function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);

  const loadReports = () => {
    setLoading(true);
    axios.get(API + '/reports')
      .then((res) => { setReports(res.data); setError(null); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadReports(); }, []);

  const openDetail = (id) => {
    setSelected(id);
    setDetail(null);
    axios.get(API + '/reports/' + id)
      .then((res) => setDetail(res.data))
      .catch((err) => setError(err.message));
  };

  const deleteReport = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this report?')) return;
    try {
      await axios.delete(API + '/reports/' + id);
      if (selected === id) { setSelected(null); setDetail(null); }
      loadReports();
    } catch (err) { alert('Delete failed: ' + err.message); }
  };

  const fmtDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <main className="ml-64 mt-16 p-8 bg-slate-50 min-h-screen">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Reports Archive</h1>
          <p className="text-sm text-slate-500 mt-1">All analyzed studies &middot; {reports.length} total</p>
        </div>
        <button onClick={loadReports} className="px-4 py-2 bg-white border border-slate-200 hover:border-slate-300 rounded-lg text-sm font-medium text-slate-700 transition-colors">
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* LEFT: List */}
        <div className="col-span-2 bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
            <div className="grid grid-cols-12 gap-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              <div className="col-span-1">ID</div>
              <div className="col-span-5">File</div>
              <div className="col-span-3">Top Finding</div>
              <div className="col-span-2">Date</div>
              <div className="col-span-1"></div>
            </div>
          </div>
          <div className="divide-y divide-slate-100 max-h-[32rem] overflow-y-auto">
            {loading && <div className="px-5 py-12 text-center text-sm text-slate-400">Loading...</div>}
            {!loading && reports.length === 0 && (
              <div className="px-5 py-16 text-center text-sm text-slate-400">
                No reports yet. Analyze a study to create one.
              </div>
            )}
            {reports.map((r) => {
              const pct = (r.confidence * 100).toFixed(1);
              const topLabel = r.top_finding || 'Unknown';
              return (
                <div
                  key={r.id}
                  onClick={() => openDetail(r.id)}
                  className={'grid grid-cols-12 gap-3 px-5 py-3 cursor-pointer hover:bg-slate-50 transition-colors ' + (selected === r.id ? 'bg-sky-50/60' : '')}
                >
                  <div className="col-span-1 text-xs font-mono text-slate-400">#{r.id}</div>
                  <div className="col-span-5 text-xs text-slate-800 truncate font-mono">{r.filename}</div>
                  <div className="col-span-3">
                    <span className={'text-xs font-semibold ' + severityColor(pct, topLabel)}>{topLabel}</span>
                    <span className={'text-[10px] font-mono ml-2 ' + severityColor(pct, topLabel)}>{pct}%</span>
                  </div>
                  <div className="col-span-2 text-[10px] text-slate-400 font-mono">{fmtDate(r.created_at)}</div>
                  <div className="col-span-1 text-right">
                    <button
                      onClick={(e) => deleteReport(r.id, e)}
                      className="text-[10px] text-red-400 hover:text-red-600 font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT: Detail */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Report Detail</div>
          </div>
          <div className="p-5">
            {!selected && <div className="py-16 text-center text-sm text-slate-400">Select a report to view</div>}
            {selected && !detail && <div className="py-16 text-center text-sm text-slate-400">Loading...</div>}
            {detail && (
              <div className="space-y-4">
                {detail.image_data_url && (
                  <div className="rounded-lg overflow-hidden bg-slate-900 border border-slate-200">
                    <img src={detail.image_data_url} alt="X-ray" className="w-full h-auto" />
                  </div>
                )}
                <div className="text-xs font-mono text-slate-500 truncate">{detail.filename}</div>
                <div className="border-t border-slate-100 pt-3 space-y-1.5">
                  {Object.entries(detail.predictions).map(([predLabel, prob]) => {
                    const pct = (prob * 100).toFixed(1);
                    return (
                      <div key={predLabel} className="flex items-center justify-between text-xs">
                        <span className="text-slate-700">{predLabel}</span>
                        <span className={'font-mono font-semibold ' + severityColor(pct, predLabel)}>{pct}%</span>
                      </div>
                    );
                  })}
                </div>
                <div className="text-[10px] font-mono text-slate-400 pt-3 border-t border-slate-100 space-y-1">
                  <div className="flex justify-between"><span>MODEL</span><span>{detail.model_version}</span></div>
                  <div className="flex justify-between"><span>INFERENCE</span><span>{detail.inference_time_ms} ms</span></div>
                  <div className="flex justify-between"><span>DIMENSIONS</span><span>{detail.image_dimensions.join(' x ')}</span></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default ReportsPage;