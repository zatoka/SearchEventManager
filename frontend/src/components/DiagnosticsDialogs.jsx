import { useCallback, useEffect, useMemo, useState } from 'react';

// Hidden troubleshooting dialogs (no visible link in the UI):
//   Ctrl + Shift + L  -> Logs
//   Ctrl + Shift + D  -> Database (schema + data, read-only)
// The backend can turn these off with DIAGNOSTICS_ENABLED=false in
// %APPDATA%\search-events-manager\.env

const API_BASE = 'http://127.0.0.1:8002/api';

const wideModal = { maxWidth: 1100, width: '95%', maxHeight: '90vh', display: 'flex', flexDirection: 'column' };
const bodyStyle = { padding: '0 20px 20px', overflow: 'auto', flex: 1 };
const mono = {
  fontFamily: 'Consolas, "Courier New", monospace', fontSize: '0.8rem',
  background: '#111', color: '#e0e0e0', padding: 12, borderRadius: 6,
  whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0,
};
const tableStyle = { borderCollapse: 'collapse', width: '100%', fontSize: '0.8rem' };
const cell = { border: '1px solid #ccc', padding: '4px 6px', textAlign: 'left', verticalAlign: 'top' };
const rowStyle = { display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 };

const formatBytes = (n) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB`
  : n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`);

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Error ${res.status}`);
  return body;
}

function Dialog({ title, labelId, onClose, children }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby={labelId}
           style={wideModal} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 id={labelId}>{title}</h2>
          <button className="modal-close" aria-label="Close" onClick={onClose}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ── Logs dialog ────────────────────────────────────────────────────────────
function LogsDialog({ onClose }) {
  const [files, setFiles] = useState([]);
  const [logDir, setLogDir] = useState('');
  const [selected, setSelected] = useState('');
  const [lines, setLines] = useState(500);
  const [filter, setFilter] = useState('');
  const [log, setLog] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadList = useCallback(async () => {
    try {
      const data = await getJson('/diagnostics/logs');
      setFiles(data.files);
      setLogDir(data.log_dir);
      setSelected(s => s || data.files[0]?.id || '');
      setError(null);
    } catch (err) { setError(err.message); }
  }, []);

  const loadLog = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    try {
      setLog(await getJson(`/diagnostics/logs/read?id=${encodeURIComponent(selected)}&lines=${lines}`));
      setError(null);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, [selected, lines]);

  useEffect(() => { loadList(); }, [loadList]);
  useEffect(() => { loadLog(); }, [loadLog]);

  const shown = useMemo(() => {
    if (!log) return '';
    if (!filter.trim()) return log.text;
    const f = filter.toLowerCase();
    return log.text.split('\n').filter(l => l.toLowerCase().includes(f)).join('\n');
  }, [log, filter]);

  return (
    <Dialog title="📜 Logs" labelId="diag-logs-title" onClose={onClose}>
      <div style={bodyStyle}>
        <div style={rowStyle}>
          <label>File{' '}
            <select value={selected} onChange={e => setSelected(e.target.value)}>
              {files.map(f => (
                <option key={f.id} value={f.id}>
                  {f.id} ({formatBytes(f.size_bytes)}, {f.modified.replace('T', ' ')})
                </option>
              ))}
            </select>
          </label>
          <label>Last{' '}
            <select value={lines} onChange={e => setLines(Number(e.target.value))}>
              {[200, 500, 2000, 5000].map(n => <option key={n} value={n}>{n} lines</option>)}
            </select>
          </label>
          <input type="text" placeholder="Filter (e.g. error, 429, venueId)"
                 value={filter} onChange={e => setFilter(e.target.value)}
                 aria-label="Filter log lines" style={{ minWidth: 220 }} />
          <button className="btn btn-secondary btn-sm" onClick={() => { loadList(); loadLog(); }}
                  disabled={loading}>
            {loading ? 'Loading...' : '🔄 Refresh'}
          </button>
          <button className="btn btn-secondary btn-sm"
                  onClick={() => navigator.clipboard?.writeText(shown)} disabled={!shown}>
            📋 Copy
          </button>
        </div>

        {error && <p className="error-msg" role="alert">⚠️ {error}</p>}
        {logDir && <p style={{ color: '#666', margin: '0 0 8px', fontSize: '0.8rem' }}>Folder: {logDir}</p>}
        {!error && files.length === 0 && <p>No log files yet.</p>}

        {log && (
          <>
            <p style={{ color: '#666', margin: '0 0 8px', fontSize: '0.8rem' }}>
              {log.returned_lines} of {log.total_lines_read} lines
              {log.truncated ? ' (showing the end of the file)' : ''} · API keys are masked
            </p>
            <pre style={{ ...mono, maxHeight: '60vh', overflow: 'auto' }}>{shown || '(no matching lines)'}</pre>
          </>
        )}
      </div>
    </Dialog>
  );
}

// ── Database dialog ────────────────────────────────────────────────────────
const PAGE_SIZE = 50;

function DatabaseDialog({ onClose }) {
  const [tab, setTab] = useState('schema');
  const [schema, setSchema] = useState(null);
  const [table, setTable] = useState('');
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const loadSchema = useCallback(async () => {
    try {
      const s = await getJson('/diagnostics/db/schema');
      setSchema(s);
      setTable(t => t || s.tables[0]?.name || '');
      setError(null);
    } catch (err) { setError(err.message); }
  }, []);

  const loadRows = useCallback(async () => {
    if (!table) return;
    try {
      setData(await getJson(`/diagnostics/db/table/${encodeURIComponent(table)}?limit=${PAGE_SIZE}&offset=${offset}`));
      setError(null);
    } catch (err) { setError(err.message); }
  }, [table, offset]);

  useEffect(() => { loadSchema(); }, [loadSchema]);
  useEffect(() => { if (tab === 'data') loadRows(); }, [tab, loadRows]);

  const current = schema?.tables.find(t => t.name === table);

  return (
    <Dialog title="🗄️ Database (read-only)" labelId="diag-db-title" onClose={onClose}>
      <div style={bodyStyle}>
        <div style={rowStyle}>
          {['schema', 'data'].map(t => (
            <button key={t} className={`btn btn-sm ${tab === t ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setTab(t)} aria-pressed={tab === t}>
              {t === 'schema' ? '📐 Schema' : '📄 Data'}
            </button>
          ))}
          <label>Table{' '}
            <select value={table} onChange={e => { setTable(e.target.value); setOffset(0); }}>
              {schema?.tables.map(t => (
                <option key={t.name} value={t.name}>{t.name} ({t.row_count} rows)</option>
              ))}
            </select>
          </label>
          <button className="btn btn-secondary btn-sm" onClick={() => { loadSchema(); if (tab === 'data') loadRows(); }}>
            🔄 Refresh
          </button>
        </div>

        {error && <p className="error-msg" role="alert">⚠️ {error}</p>}
        {schema && (
          <p style={{ color: '#666', margin: '0 0 10px', fontSize: '0.8rem' }}>
            {schema.db_path} · {formatBytes(schema.size_bytes)} · modified {schema.modified.replace('T', ' ')}
          </p>
        )}

        {tab === 'schema' && schema && (
          <>
            <h3 style={{ margin: '6px 0' }}>All tables</h3>
            <table style={{ ...tableStyle, marginBottom: 16 }}>
              <thead><tr><th style={cell}>Table</th><th style={cell}>Rows</th><th style={cell}>Columns</th></tr></thead>
              <tbody>
                {schema.tables.map(t => (
                  <tr key={t.name} onClick={() => setTable(t.name)}
                      style={{ cursor: 'pointer', background: t.name === table ? '#e9e3fb' : undefined }}>
                    <td style={cell}>{t.name}</td><td style={cell}>{t.row_count}</td><td style={cell}>{t.columns.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {current && (
              <>
                <h3 style={{ margin: '6px 0' }}>{current.name} - columns</h3>
                <table style={{ ...tableStyle, marginBottom: 16 }}>
                  <thead>
                    <tr>{['Column', 'Type', 'Primary key', 'Not null', 'Default'].map(h => <th key={h} style={cell}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {current.columns.map(c => (
                      <tr key={c.name}>
                        <td style={cell}>{c.name}</td><td style={cell}>{c.type || '-'}</td>
                        <td style={cell}>{c.primary_key ? '✓' : ''}</td><td style={cell}>{c.not_null ? '✓' : ''}</td>
                        <td style={cell}>{c.default ?? ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <h3 style={{ margin: '6px 0' }}>Definition</h3>
                <pre style={mono}>
                  {[current.create_sql, ...current.indexes.map(i => i.sql).filter(Boolean)].join(';\n\n')}
                </pre>
              </>
            )}
          </>
        )}

        {tab === 'data' && data && (
          <>
            <div style={rowStyle}>
              <button className="btn btn-secondary btn-sm" disabled={offset === 0}
                      onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>← Previous</button>
              <span>
                Rows {data.total === 0 ? 0 : offset + 1}-{Math.min(offset + PAGE_SIZE, data.total)} of {data.total}
              </span>
              <button className="btn btn-secondary btn-sm" disabled={offset + PAGE_SIZE >= data.total}
                      onClick={() => setOffset(offset + PAGE_SIZE)}>Next →</button>
            </div>
            <div style={{ overflow: 'auto', maxHeight: '58vh' }}>
              <table style={tableStyle}>
                <thead>
                  <tr>{data.columns.map(c => <th key={c} style={{ ...cell, position: 'sticky', top: 0, background: '#ddd' }}>{c}</th>)}</tr>
                </thead>
                <tbody>
                  {data.rows.map((r, i) => (
                    <tr key={i}>
                      {r.map((v, j) => (
                        <td key={j} style={{ ...cell, maxWidth: 320 }} title={v == null ? 'NULL' : String(v)}>
                          {v == null ? <em style={{ color: '#999' }}>NULL</em>
                            : String(v).length > 120 ? `${String(v).slice(0, 120)}…` : String(v)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </Dialog>
  );
}

// ── Hotkey listener ────────────────────────────────────────────────────────
export default function DiagnosticsDialogs() {
  const [open, setOpen] = useState(null);   // 'logs' | 'db' | null

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { setOpen(null); return; }
      if (!e.ctrlKey || !e.shiftKey || e.altKey) return;
      const key = e.key.toLowerCase();
      if (key === 'l') { e.preventDefault(); setOpen(o => (o === 'logs' ? null : 'logs')); }
      if (key === 'd') { e.preventDefault(); setOpen(o => (o === 'db' ? null : 'db')); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  if (open === 'logs') return <LogsDialog onClose={() => setOpen(null)} />;
  if (open === 'db') return <DatabaseDialog onClose={() => setOpen(null)} />;
  return null;
}
