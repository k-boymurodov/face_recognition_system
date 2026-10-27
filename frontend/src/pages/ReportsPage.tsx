import { useEffect, useState } from 'react';
import { Download, FileSpreadsheet, Filter, RefreshCw } from 'lucide-react';
import { api, getApiError } from '../services/api';
import type { AttendanceEvent, Employee } from '../types';

function dayOffset(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function time(value?: string | null) {
  if (!value) return '—';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value.slice(0, 5) : parsed.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' });
}

export default function ReportsPage() {
  const [start, setStart] = useState(dayOffset(0));
  const [end, setEnd] = useState(dayOffset(0));
  const [employeeId, setEmployeeId] = useState('');
  const [department, setDepartment] = useState('');
  const [period, setPeriod] = useState<'day' | 'week' | 'month' | 'custom'>('day');
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [rows, setRows] = useState<AttendanceEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { void api.employees().then(setEmployees).catch((cause) => setError(getApiError(cause))); }, []);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ start_date: start, end_date: end });
      if (employeeId) params.set('employee_id', employeeId);
      if (department) params.set('department', department);
      const response = await fetch(`/api/attendance?${params}`, { credentials: 'include' });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.detail || 'Hisobotni yuklab bo‘lmadi.');
      setRows(payload as AttendanceEvent[]);
    } catch (cause) { setError(getApiError(cause)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  const totalMinutes = rows.reduce((total, row) => total + (row.work_minutes || 0), 0);
  const exportHref = api.exportUrl(start, end) + (employeeId ? `&employee_id=${encodeURIComponent(employeeId)}` : '') + (department ? `&department=${encodeURIComponent(department)}` : '');

  function choosePeriod(value: 'day' | 'week' | 'month' | 'custom') {
    setPeriod(value);
    const today = dayOffset(0);
    if (value === 'day') { setStart(today); setEnd(today); }
    if (value === 'week') { setStart(dayOffset(-6)); setEnd(today); }
    if (value === 'month') {
      const first = new Date();
      first.setDate(1);
      setStart(new Date(first.getTime() - first.getTimezoneOffset() * 60000).toISOString().slice(0, 10));
      setEnd(today);
    }
  }

  return <>
    <div className="page-heading"><div><div className="eyebrow">Tahlil va nazorat</div><h1>Hisobotlar</h1><p>MySQL bazasidagi kunlik va sana oralig‘i davomat yozuvlari.</p></div><a className="button primary" href={exportHref}><Download size={15} /> CSV yuklab olish</a></div>
    <section className="panel" style={{ marginBottom: 15 }}><div className="panel-head"><div><h2><Filter size={14} style={{ verticalAlign: 'middle', marginRight: 7 }} />Hisobot filtrlari</h2><p>Sana, xodim va bo‘limni belgilang</p></div></div><div className="panel-body"><div className="toolbar" style={{ margin: 0 }}>
      <select className="select-field" aria-label="Hisobot davri" value={period} onChange={(event) => choosePeriod(event.target.value as typeof period)}><option value="day">Bugun</option><option value="week">Hafta</option><option value="month">Oy</option><option value="custom">Sana oralig‘i</option></select>
      <div className="filter-date"><label htmlFor="report-start">Dan</label><input className="field" id="report-start" type="date" value={start} onChange={(event) => { setStart(event.target.value); setPeriod('custom'); }} /></div>
      <div className="filter-date"><label htmlFor="report-end">Gacha</label><input className="field" id="report-end" type="date" value={end} onChange={(event) => { setEnd(event.target.value); setPeriod('custom'); }} /></div>
      <select className="select-field" aria-label="Xodim filtri" value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}><option value="">Barcha xodimlar</option>{employees.map((employee) => <option value={employee.id} key={employee.id}>{employee.name}</option>)}</select>
      <select className="select-field" aria-label="Bo‘lim filtri" value={department} onChange={(event) => setDepartment(event.target.value)}><option value="">Barcha bo‘limlar</option>{[...new Set(employees.map((employee) => employee.department).filter((item): item is string => Boolean(item)))].sort().map((item) => <option key={item}>{item}</option>)}</select>
      <button className="button primary" onClick={() => void load()} disabled={loading}><RefreshCw size={14} />{loading ? 'Yuklanmoqda…' : 'Hisobotni ko‘rsatish'}</button>
    </div></div></section>
    {error && <div className="error-banner">{error}</div>}
    <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
      <article className="stat-card"><div className="stat-top">Davomat yozuvlari<FileSpreadsheet size={16} color="#2563eb" /></div><div className="stat-value">{rows.length}</div><div className="stat-caption">Tanlangan davrda qayd qilingan</div></article>
      <article className="stat-card"><div className="stat-top">Kirish qaydlari<Filter size={16} color="#17865d" /></div><div className="stat-value">{rows.filter((row) => Boolean(row.entry_time)).length}</div><div className="stat-caption">Haqiqiy bazadagi yozuvlar</div></article>
      <article className="stat-card"><div className="stat-top">Jami ish vaqti<RefreshCw size={16} color="#b7791f" /></div><div className="stat-value">{Math.floor(totalMinutes / 60)} soat</div><div className="stat-caption">Chiqish qaydi bo‘lgan yozuvlar yig‘indisi</div></article>
    </div>
    <section className="panel table-panel"><div className="panel-head"><div><h2>Davomat tafsilotlari</h2><p>{start} — {end}</p></div><span className="status-pill">{rows.length} yozuv</span></div>
      {loading ? <div className="panel-body" style={{ display: 'grid', gap: 13 }}>{Array.from({ length: 5 }, (_, index) => <div className="skeleton" key={index} />)}</div> : rows.length ? <div className="table-wrap"><table><thead><tr><th>Sana</th><th>Xodim</th><th>Bo‘lim</th><th>Kirish</th><th>Chiqish</th><th>Ish vaqti</th><th>Holat</th></tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.employee_id}-${String(row.date)}-${index}`}><td>{row.date ? new Date(`${String(row.date)}T12:00:00`).toLocaleDateString('uz-UZ') : '—'}</td><td><div className="person-cell"><span className="person-initial">{row.name.slice(0, 1)}</span><span><span className="person-primary">{row.name}</span><span className="person-secondary">{row.employee_code || row.employee_id}</span></span></div></td><td>{row.department || 'Belgilanmagan'}</td><td>{time(row.entry_time)}</td><td>{time(row.exit_time)}</td><td>{row.work_minutes != null ? `${Math.floor(row.work_minutes / 60)} soat ${row.work_minutes % 60} daq.` : '—'}</td><td><span className={`status-pill ${row.status === 'late' ? 'late' : ''}`}>{row.status === 'late' ? 'Kechikdi' : row.entry_time ? 'Kelgan' : 'Kelmagan'}</span></td></tr>)}</tbody></table></div> : <div className="empty-state"><FileSpreadsheet size={25} /><strong>Tanlangan davrda yozuv topilmadi</strong><p>Sana oralig‘ini yoki filtrlarni o‘zgartiring.</p></div>}
    </section>
  </>;
}
