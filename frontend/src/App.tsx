import { useEffect, useState } from 'react';
import { Activity, Bell, CalendarDays, ChartNoAxesCombined, ChevronDown, LayoutDashboard, LogOut, Menu, Moon, Search, Sun, Users, Landmark, X } from 'lucide-react';
import DashboardPage from './pages/DashboardPage';
import EmployeesPage from './pages/EmployeesPage';
import AttendancePage from './pages/AttendancePage';
import ReportsPage from './pages/ReportsPage';
import LoginPage from './pages/LoginPage';
import { api, getApiError } from './services/api';
import type { Role, User } from './types';

type Page = 'overview' | 'employees' | 'attendance' | 'reports';
type ToastItem = { id: number; message: string; kind: 'success' | 'error' };

const navigation: { id: Page; title: string; icon: typeof LayoutDashboard; roles: Role[] }[] = [
  { id: 'overview', title: 'Bosh sahifa', icon: LayoutDashboard, roles: ['admin', 'operator', 'reports'] },
  { id: 'employees', title: 'Xodimlar', icon: Users, roles: ['admin', 'operator', 'reports'] },
  { id: 'attendance', title: 'Davomat', icon: CalendarDays, roles: ['admin', 'operator'] },
  { id: 'reports', title: 'Hisobotlar', icon: ChartNoAxesCombined, roles: ['admin', 'operator', 'reports'] },
];
const roleNames: Record<Role, string> = { admin: 'Administrator', operator: 'Operator', reports: 'Hisobot kuzatuvchisi' };

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [page, setPage] = useState<Page>('overview');
  const [search, setSearch] = useState('');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => localStorage.getItem('attendance-theme') === 'dark' ? 'dark' : 'light');
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('attendance-theme', theme);
  }, [theme]);

  useEffect(() => {
    let active = true;
    api.me().then(({ user: current }) => { if (active) setUser(current); }).catch(() => undefined).finally(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, []);

  function notify(message: string, kind: 'success' | 'error' = 'success') {
    const id = Date.now() + Math.random();
    setToasts((items) => [...items, { id, message, kind }]);
    window.setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 4200);
  }

  async function logout() {
    try { await api.logout(); } catch (error) { notify(getApiError(error), 'error'); }
    setUser(null);
    setPage('overview');
  }

  if (checking) return <main className="login-page"><div className="login-form-wrap"><div className="skeleton" style={{ width: 250, height: 18 }} /></div></main>;
  if (!user) return <LoginPage onLogin={setUser} />;

  const visibleNavigation = navigation.filter((item) => item.roles.includes(user.role));
  const today = new Date().toLocaleDateString('uz-UZ', { day: 'numeric', month: 'short', year: 'numeric' });

  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
      <div className="brand"><span className="brand-mark"><Landmark size={17} /></span><span className="brand-name">BANK DAVOMAT<span className="brand-sub">ICHKI BOSHQARUV TIZIMI</span></span><button className="icon-button mobile-menu" style={{ marginLeft: 'auto', color: 'white', background: 'transparent', borderColor: 'rgba(255,255,255,.18)' }} onClick={() => setMobileOpen(false)} aria-label="Menyuni yopish"><X size={15} /></button></div>
      <div className="nav-label">Ish maydoni</div><nav className="nav-list">{visibleNavigation.map(({ id, title, icon: Icon }) => <button key={id} className={`nav-item ${page === id ? 'active' : ''}`} onClick={() => { setPage(id); setMobileOpen(false); }}><Icon size={17} />{title}</button>)}</nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-foot"><strong>Davomat nazorati</strong>Yuz ma’lumotlari himoyalangan serverda qayta ishlanadi.<br />UTC+05 · Toshkent</div>
    </aside>
    <main className="main-area">
      <header className="topbar">
        <div className="topbar-left"><button className="icon-button mobile-menu" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Menyuni ochish"><Menu size={17} /></button><label className="top-search"><Search size={15} /><input placeholder={page === 'employees' ? 'Xodimlarni qidirish…' : 'Xodimlarni qidirish'} value={search} onChange={(event) => setSearch(event.target.value)} onFocus={() => { if (page !== 'employees') setPage('employees'); }} aria-label="Xodimlarni qidirish" /></label><span className="top-date search-hide-mobile">{today}</span></div>
        <div className="topbar-right"><button className="icon-button" title={theme === 'light' ? 'Tungi rejim' : 'Kunduzgi rejim'} aria-label="Rang rejimini almashtirish" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>{theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}</button><button className="icon-button" title="Bildirishnomalar" aria-label="Bildirishnomalar" onClick={() => notify('Yangi tizim bildirishnomasi yo‘q.')}><Bell size={15} /></button><div className="user-chip"><span className="avatar">{user.username.slice(0, 1).toUpperCase()}</span><span className="user-name search-hide-mobile">{user.username}<span className="user-role">{roleNames[user.role]}</span></span><button className="icon-button" title="Tizimdan chiqish" aria-label="Tizimdan chiqish" onClick={() => void logout()}><LogOut size={14} /></button><ChevronDown size={12} color="var(--muted)" className="search-hide-mobile" /></div></div>
      </header>
      <div className="page-content" key={page}>
        {page === 'overview' && <DashboardPage />}
        {page === 'employees' && <EmployeesPage query={search} role={user.role} notify={notify} />}
        {page === 'attendance' && <AttendancePage notify={notify} />}
        {page === 'reports' && <ReportsPage />}
      </div>
    </main>
    <div className="toast-region" aria-live="polite">{toasts.map((toast) => <div className={`toast ${toast.kind === 'error' ? 'error' : ''}`} key={toast.id}>{toast.kind === 'error' ? <Activity size={15} color="#c24143" /> : <Activity size={15} color="#17865d" />}{toast.message}</div>)}</div>
  </div>;
}
