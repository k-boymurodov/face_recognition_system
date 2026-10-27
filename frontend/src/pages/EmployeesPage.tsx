import { useEffect, useState } from 'react';
import { Camera, Check, ChevronRight, Edit3, Plus, Search, Shield, Trash2, UserRound, X } from 'lucide-react';
import CameraCapture from '../components/CameraCapture';
import { api, getApiError } from '../services/api';
import type { Employee, Role } from '../types';

interface EmployeesPageProps {
  query: string;
  role: Role;
  notify: (message: string, kind?: 'success' | 'error') => void;
}

type FormState = {
  employee_code: string;
  name: string;
  department: string;
  position: string;
  phone: string;
  status: 'active' | 'inactive';
};

const emptyForm: FormState = { employee_code: '', name: '', department: '', position: '', phone: '', status: 'active' };

function EmployeeForm({ initial, busy, onSave, onCancel }: { initial: FormState; busy: boolean; onSave: (value: FormState) => void; onCancel: () => void }) {
  const [form, setForm] = useState(initial);
  function change<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }
  return <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="employee-form-title">
    <div className="modal-head"><div><h2 id="employee-form-title">{initial.employee_code ? 'Xodim ma’lumotlarini tahrirlash' : 'Yangi xodim'}</h2><p>Ma’lumotlar kompaniya davomat bazasiga yoziladi.</p></div><button className="icon-button" onClick={onCancel} aria-label="Yopish"><X size={16} /></button></div>
    <form className="modal-body" onSubmit={(event) => { event.preventDefault(); onSave(form); }}>
      <div className="form-grid">
        <div className="form-field"><label htmlFor="employee-code">Xodim ID raqami</label><input id="employee-code" required maxLength={64} value={form.employee_code} onChange={(event) => change('employee_code', event.target.value)} placeholder="BK-00124" /></div>
        <div className="form-field"><label htmlFor="employee-name">F.I.Sh.</label><input id="employee-name" required minLength={2} value={form.name} onChange={(event) => change('name', event.target.value)} placeholder="Ism Familiya" /></div>
        <div className="form-field"><label htmlFor="employee-department">Bo‘lim</label><input id="employee-department" required value={form.department} onChange={(event) => change('department', event.target.value)} placeholder="Chakana bank xizmatlari" /></div>
        <div className="form-field"><label htmlFor="employee-position">Lavozim</label><input id="employee-position" required value={form.position} onChange={(event) => change('position', event.target.value)} placeholder="Bosh mutaxassis" /></div>
        <div className="form-field"><label htmlFor="employee-phone">Telefon raqami · ixtiyoriy</label><input id="employee-phone" type="tel" value={form.phone} onChange={(event) => change('phone', event.target.value)} placeholder="+998 90 000 00 00" /></div>
        <div className="form-field"><label htmlFor="employee-status">Holat</label><select id="employee-status" value={form.status} onChange={(event) => change('status', event.target.value as FormState['status'])}><option value="active">Faol</option><option value="inactive">Faol emas</option></select></div>
      </div>
      <div className="modal-actions"><button type="button" className="button" onClick={onCancel}>Bekor qilish</button><button type="submit" className="button primary" disabled={busy}>{busy ? 'Saqlanmoqda…' : 'Saqlash'}</button></div>
    </form>
  </section></div>;
}

export default function EmployeesPage({ query, role, notify }: EmployeesPageProps) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [positionFilter, setPositionFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [formEmployee, setFormEmployee] = useState<Employee | null | false>(false);
  const [busy, setBusy] = useState(false);
  const [cameraEmployee, setCameraEmployee] = useState<number | null>(null);
  const [profile, setProfile] = useState<Employee | null>(null);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);

  async function load() {
    setLoading(true);
    setError('');
    try { setEmployees(await api.employees(query)); }
    catch (cause) { setError(getApiError(cause)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [query]);

  const departments = [...new Set(employees.map((person) => person.department).filter((value): value is string => Boolean(value)))].sort();
  const positions = [...new Set(employees.map((person) => person.position).filter((value): value is string => Boolean(value)))].sort();
  const filtered = employees.filter((person) => (departmentFilter === 'all' || person.department === departmentFilter) && (positionFilter === 'all' || person.position === positionFilter) && (statusFilter === 'all' || person.status === statusFilter));
  const canEdit = role === 'admin';

  async function save(value: FormState) {
    setBusy(true);
    try {
      if (formEmployee && typeof formEmployee === 'object') {
        await api.updateEmployee(formEmployee.id, value);
        notify('Xodim ma’lumotlari yangilandi.');
        setFormEmployee(false);
        await load();
      } else {
        const result = await api.createEmployee({ ...value, phone: value.phone || null });
        setFormEmployee(false);
        setCameraEmployee(result.id);
        notify('Xodim yaratildi. Endi yuzini kamerada ro‘yxatdan o‘tkazing.');
        await load();
      }
    } catch (cause) { notify(getApiError(cause), 'error'); }
    finally { setBusy(false); }
  }

  async function toggleStatus(employee: Employee) {
    try {
      await api.updateEmployee(employee.id, { status: employee.status === 'active' ? 'inactive' : 'active' });
      notify(employee.status === 'active' ? 'Xodim faol emas holatiga o‘tkazildi.' : 'Xodim faollashtirildi.');
      await load();
    } catch (cause) { notify(getApiError(cause), 'error'); }
  }

  async function remove(employee: Employee) {
    if (!window.confirm(`${employee.name} xodimini va unga bog‘liq davomat tarixini o‘chirasizmi? Bu amalni ortga qaytarib bo‘lmaydi.`)) return;
    try { await api.deleteEmployee(employee.id); notify('Xodim o‘chirildi.'); await load(); }
    catch (cause) { notify(getApiError(cause), 'error'); }
  }

  async function openProfile(employee: Employee) {
    setProfile(employee);
    try { setHistory(await api.employeeHistory(employee.id)); }
    catch (cause) { notify(getApiError(cause), 'error'); }
  }

  return <>
    <div className="page-heading"><div><div className="eyebrow">Xodimlar reyestri</div><h1>Xodimlar</h1><p>Profil, yuz ro‘yxati va faollik holatini boshqaring.</p></div>{canEdit && <button className="button primary" onClick={() => setFormEmployee(null)}><Plus size={15} /> Yangi xodim</button>}</div>
    {error && <div className="error-banner">{error}</div>}
    <div className="toolbar">
      <label className="top-search search-field"><Search size={15} /><input aria-label="Xodimlarni qidirish" placeholder="Ism, ID, bo‘lim yoki lavozim…" value={query} readOnly /></label>
      <select className="select-field" aria-label="Bo‘lim filtri" value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)}><option value="all">Barcha bo‘limlar</option>{departments.map((item) => <option key={item}>{item}</option>)}</select>
      <select className="select-field" aria-label="Lavozim filtri" value={positionFilter} onChange={(event) => setPositionFilter(event.target.value)}><option value="all">Barcha lavozimlar</option>{positions.map((item) => <option key={item}>{item}</option>)}</select>
      <select className="select-field" aria-label="Holat filtri" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="all">Barcha holatlar</option><option value="active">Faol</option><option value="inactive">Faol emas</option></select>
      <span className="top-date">{filtered.length} ta xodim</span>
    </div>
    <section className="panel table-panel">
      <div className="table-wrap"><table><thead><tr><th>Xodim</th><th>Bo‘lim / lavozim</th><th>Telefon</th><th>Yuz</th><th>Holat</th><th>Amallar</th></tr></thead><tbody>
        {loading ? Array.from({ length: 5 }, (_, index) => <tr key={index}><td colSpan={6}><div className="skeleton" style={{ width: '78%' }} /></td></tr>) : filtered.map((employee) => <tr key={employee.id}>
          <td><div className="person-cell"><span className="person-initial">{employee.name.slice(0, 1)}</span><span><span className="person-primary">{employee.name}</span><span className="person-secondary">ID {employee.employee_code || employee.id}</span></span></div></td>
          <td><span className="person-primary">{employee.department || 'Belgilanmagan'}</span><span className="person-secondary">{employee.position || 'Lavozim kiritilmagan'}</span></td>
          <td>{employee.phone || '—'}</td><td>{employee.has_face ? <span className="status-pill"><Check size={12} /> Ro‘yxatda</span> : <span className="status-pill late">Kiritilmagan</span>}</td>
          <td><span className={`status-pill ${employee.status === 'inactive' ? 'inactive' : ''}`}>{employee.status === 'active' ? 'Faol' : 'Faol emas'}</span></td>
          <td><div style={{ display: 'flex', gap: 5 }}><button className="icon-button" title="Profil va davomat tarixi" aria-label="Profil" onClick={() => void openProfile(employee)}><ChevronRight size={15} /></button>{canEdit && <><button className="icon-button" title="Yuzni ro‘yxatdan o‘tkazish" aria-label="Yuzni ro‘yxatdan o‘tkazish" onClick={() => setCameraEmployee(employee.id)}><Camera size={14} /></button><button className="icon-button" title="Tahrirlash" aria-label="Tahrirlash" onClick={() => setFormEmployee(employee)}><Edit3 size={14} /></button><button className="icon-button" title={employee.status === 'active' ? 'Faolsizlantirish' : 'Faollashtirish'} aria-label="Holatni o‘zgartirish" onClick={() => void toggleStatus(employee)}><Shield size={14} /></button><button className="icon-button" title="O‘chirish" aria-label="O‘chirish" onClick={() => void remove(employee)}><Trash2 size={14} /></button></>}</div></td>
        </tr>)}
      </tbody></table>{!loading && !filtered.length && <div className="empty-state"><UserRound size={26} /><strong>Xodim topilmadi</strong><p>Qidiruv yoki filtr shartlarini o‘zgartiring.</p></div>}</div>
    </section>
    {formEmployee !== false && <EmployeeForm initial={formEmployee ? { employee_code: formEmployee.employee_code || '', name: formEmployee.name, department: formEmployee.department || '', position: formEmployee.position || '', phone: formEmployee.phone || '', status: formEmployee.status } : emptyForm} busy={busy} onSave={(value) => void save(value)} onCancel={() => setFormEmployee(false)} />}
    {cameraEmployee !== null && <CameraCapture employeeId={cameraEmployee} onCancel={() => setCameraEmployee(null)} onComplete={(message) => { setCameraEmployee(null); notify(message); void load(); }} />}
          {profile && <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true"><div className="modal-head"><div><h2>{profile.name}</h2><p>{profile.employee_code || `ID ${profile.id}`} · {profile.department || 'Bo‘lim belgilanmagan'} · {profile.position || 'Lavozim belgilanmagan'}</p></div><button className="icon-button" onClick={() => setProfile(null)} aria-label="Yopish"><X size={16} /></button></div><div className="modal-body"><div className="form-grid"><div><div className="person-secondary">Telefon</div><strong>{profile.phone || 'Kiritilmagan'}</strong></div><div><div className="person-secondary">Yuz ro‘yxatdan o‘tgan sana</div><strong>{profile.face_registered_at ? new Date(profile.face_registered_at).toLocaleDateString('uz-UZ') : 'Ro‘yxatdan o‘tmagan'}</strong></div><div><div className="person-secondary">Yaratilgan sana</div><strong>{profile.created_at ? new Date(profile.created_at).toLocaleDateString('uz-UZ') : '—'}</strong></div><div><div className="person-secondary">Holat</div><strong>{profile.status === 'active' ? 'Faol' : 'Faol emas'}</strong></div></div><h3 style={{ margin: '22px 0 9px', font: '700 12px Manrope' }}>Davomat tarixi · oxirgi 30 kun</h3><div className="table-wrap"><table><thead><tr><th>Vaqt</th><th>Hodisa</th><th>Ishonchlilik</th></tr></thead><tbody>{history.map((event, index) => <tr key={String(event.id ?? index)}><td>{event.timestamp ? new Date(String(event.timestamp)).toLocaleString('uz-UZ') : '—'}</td><td>{event.action === 'entry' ? 'Kirish' : 'Chiqish'}</td><td>{event.confidence != null ? `${Math.round(Number(event.confidence))}%` : '—'}</td></tr>)}</tbody></table>{!history.length && <div className="empty-state"><p>Davomat hodisalari yo‘q.</p></div>}</div></div></section></div>}
  </>;
}
