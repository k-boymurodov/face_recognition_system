import { useState } from 'react';
import { Eye, EyeOff, Landmark, LockKeyhole } from 'lucide-react';
import { api, getApiError } from '../services/api';
import type { User } from '../types';

export default function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const result = await api.login(username.trim(), password);
      onLogin(result.user);
    } catch (cause) { setError(getApiError(cause)); }
    finally { setLoading(false); }
  }

  return <main className="login-page">
    <section className="login-aside"><div className="brand"><span className="brand-mark"><Landmark size={18} /></span><span className="brand-name">BANK DAVOMAT<span className="brand-sub">ICHKI BOSHQARUV TIZIMI</span></span></div><div><div className="eyebrow" style={{ color: '#83adff' }}>Xavfsiz kirish nazorati</div><h1>Xodimlar va davomat. Bir boshqaruv markazida.</h1><p>Bankning ichki davomat tizimiga faqat vakolatli foydalanuvchilar kira oladi.</p></div><span style={{ position: 'relative', zIndex: 1, color: '#8295b0', fontSize: 10 }}>Asia/Tashkent · Xavfsiz sessiya</span></section>
    <section className="login-form-wrap"><form className="login-form" onSubmit={(event) => void submit(event)}><div className="eyebrow">Bank xodimlari platformasi</div><h2>Tizimga kirish</h2><p>Davom etish uchun hisob ma’lumotlaringizni kiriting.</p>
      {error && <div className="error-banner" role="alert">{error}</div>}
      <div className="form-field"><label htmlFor="login-user">Login</label><input id="login-user" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Foydalanuvchi nomi" /></div>
      <div className="form-field"><label htmlFor="login-password">Parol</label><div style={{ position: 'relative' }}><input id="login-password" style={{ paddingRight: 43 }} type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Parolingiz" /><button type="button" className="icon-button" style={{ position: 'absolute', right: 4, top: 2, width: 34, height: 34, border: 0 }} onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Parolni yashirish' : 'Parolni ko‘rsatish'}>{showPassword ? <EyeOff size={15} /> : <Eye size={15} />}</button></div></div>
      <button type="submit" className="button primary" disabled={loading}><LockKeyhole size={15} />{loading ? 'Tekshirilmoqda…' : 'Xavfsiz kirish'}</button>
      <p style={{ marginTop: 20, fontSize: 10 }}>Admin hisobi `.env` ichidagi bootstrap sozlamalaridan olinadi.</p>
    </form></section>
  </main>;
}
