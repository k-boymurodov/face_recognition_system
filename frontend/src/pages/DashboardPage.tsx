import { useEffect, useState } from 'react';
import { Activity, ArrowDownLeft, ArrowUpRight, Clock3, Users, UserX, CalendarCheck2, RefreshCw } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, BarChart, Bar } from 'recharts';
import { api, getApiError } from '../services/api';
import type { DashboardStats } from '../types';

function todayLocal() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function formatTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value.slice(0, 5) : date.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' });
}

function SkeletonDashboard() {
  return <><div className="stats-grid">{Array.from({ length: 6 }, (_, index) => <div className="stat-card skeleton skeleton-card" key={index} />)}</div><div className="dashboard-grid"><div className="panel skeleton" style={{ height: 310 }} /><div className="panel skeleton" style={{ height: 310 }} /></div></>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(todayLocal());

  async function load() {
    setLoading(true);
    setError('');
    try {
      setStats(await api.dashboard(selectedDate));
    } catch (cause) {
      setError(getApiError(cause));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [selectedDate]);

  const cards = stats ? [
    { label: 'Jami xodimlar', value: stats.total_employees, icon: Users, note: 'Faol xodimlar' },
    { label: 'Bugun kelganlar', value: stats.present, icon: CalendarCheck2, note: 'Davomat qaydi mavjud' },
    { label: 'Hozir ishda', value: stats.working, icon: Activity, note: 'Chiqish qayd etilmagan' },
    { label: 'Kechikkanlar', value: stats.late, icon: Clock3, note: 'Bugungi holat' },
    { label: 'Kelmaganlar', value: stats.absent, icon: UserX, note: 'Faol xodimlar ichida' },
    { label: 'Kirish / chiqish', value: `${stats.entries} / ${stats.exits}`, icon: ArrowUpRight, note: 'Bugungi hodisalar' },
  ] : [];

  return <>
    <div className="page-heading">
      <div><div className="eyebrow">Boshqaruv markazi</div><h1>Umumiy ko‘rinish</h1><p>Bank xodimlari davomatining bugungi holati.</p></div>
      <div className="filter-date"><input className="field" aria-label="Dashboard sanasi" type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} /><button className="icon-button" aria-label="Yangilash" title="Yangilash" onClick={() => void load()}><RefreshCw size={15} /></button></div>
    </div>
    {error && <div className="error-banner">{error} Ma’lumotlar bazasi ulanishini tekshiring.</div>}
    {loading && !stats ? <SkeletonDashboard /> : stats && <>
      <div className="stats-grid">{cards.map(({ label, value, icon: Icon, note }) => <article className="stat-card" key={label}><div className="stat-top"><span>{label}</span><span className="stat-icon"><Icon size={15} /></span></div><div className="stat-value">{value}</div><div className="stat-caption">{note}</div></article>)}</div>
      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-head"><div><h2>Haftalik davomat</h2><p>Oxirgi yetti kun bo‘yicha kelgan xodimlar</p></div><span className="legend"><span><i className="legend-dot" /> Kelganlar</span></span></div>
          <div className="panel-body chart-wrap"><ResponsiveContainer width="100%" height="100%"><LineChart data={stats.weekly} margin={{ top: 8, right: 10, left: -22, bottom: 0 }}><CartesianGrid stroke="var(--line)" strokeDasharray="3 4" vertical={false} /><XAxis dataKey="day" tickFormatter={(value) => new Date(`${value}T12:00:00`).toLocaleDateString('uz-UZ', { weekday: 'short' })} tick={{ fill: 'var(--muted)', fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis allowDecimals={false} tick={{ fill: 'var(--muted)', fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 5, color: 'var(--text)', fontSize: 11 }} labelFormatter={(value) => new Date(`${value}T12:00:00`).toLocaleDateString('uz-UZ')} /><Line type="monotone" dataKey="present" name="Kelganlar" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3, fill: '#2563eb' }} activeDot={{ r: 5 }} /></LineChart></ResponsiveContainer></div>
        </section>
        <section className="panel">
          <div className="panel-head"><div><h2>Bo‘limlar kesimida</h2><p>Faol xodimlar taqsimoti</p></div></div>
          <div className="panel-body chart-wrap compact"><ResponsiveContainer width="100%" height="100%"><BarChart data={stats.departments} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}><CartesianGrid stroke="var(--line)" strokeDasharray="3 4" horizontal={false} /><XAxis type="number" allowDecimals={false} hide /><YAxis type="category" dataKey="department" width={102} tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 5, color: 'var(--text)', fontSize: 11 }} /><Bar dataKey="total" name="Xodimlar" fill="#2563eb" radius={[0, 3, 3, 0]} barSize={14} /></BarChart></ResponsiveContainer></div>
        </section>
      </div>
      <section className="panel table-panel" style={{ marginTop: 15 }}>
        <div className="panel-head"><div><h2>Oxirgi hodisalar</h2><p>Bugun qayd qilingan kirish va chiqishlar</p></div><span className="status-pill">{stats.recent_events.length} ta hodisa</span></div>
        {stats.recent_events.length ? <div className="table-wrap"><table><thead><tr><th>Xodim</th><th>Bo‘lim</th><th>Hodisa</th><th>Vaqt</th><th>Ishonchlilik</th></tr></thead><tbody>{stats.recent_events.map((event) => <tr key={event.id}><td><div className="person-cell"><span className="person-initial">{event.name.slice(0, 1)}</span><span><span className="person-primary">{event.name}</span><span className="person-secondary">ID {event.employee_code ?? event.employee_id}</span></span></div></td><td>{event.department || 'Belgilanmagan'}</td><td><span className={`status-pill ${event.action === 'exit' ? 'exit' : ''}`}>{event.action === 'exit' ? <><ArrowDownLeft size={12} /> Chiqish</> : <><ArrowUpRight size={12} /> Kirish</>}</span></td><td>{formatTime(event.timestamp)}</td><td>{event.confidence != null ? `${Math.round(event.confidence)}%` : '—'}</td></tr>)}</tbody></table></div> : <div className="empty-state"><Activity size={25} /><strong>Hozircha hodisa yo‘q</strong><p>Kamera orqali davomat qayd etilganda shu yerda ko‘rinadi.</p></div>}
      </section>
      <section className="panel table-panel" style={{ marginTop: 15 }}>
        <div className="panel-head"><div><h2>Bugungi xodimlar</h2><p>Kelgan va chiqib ketgan xodimlar ro‘yxati</p></div></div>
        {stats.today_employees.length ? <div className="table-wrap"><table><thead><tr><th>Xodim</th><th>Bo‘lim</th><th>Kelish</th><th>Ketish</th><th>Holat</th></tr></thead><tbody>{stats.today_employees.map((employee) => <tr key={employee.employee_id}><td><div className="person-cell"><span className="person-initial">{employee.name.slice(0, 1)}</span><span><span className="person-primary">{employee.name}</span><span className="person-secondary">ID {employee.employee_code ?? employee.employee_id}</span></span></div></td><td>{employee.department || 'Belgilanmagan'}</td><td>{formatTime(employee.entry_time)}</td><td>{formatTime(employee.exit_time)}</td><td><span className={`status-pill ${employee.entry_time ? employee.exit_time ? 'exit' : '' : 'absent'}`}>{employee.exit_time ? 'Chiqib ketgan' : employee.entry_time ? 'Ishda' : 'Kelmagan'}</span></td></tr>)}</tbody></table></div> : <div className="empty-state"><Users size={25} /><strong>Xodimlar topilmadi</strong><p>Baza ulanishi va xodimlar ro‘yxatini tekshiring.</p></div>}
      </section>
    </>}
  </>;
}
