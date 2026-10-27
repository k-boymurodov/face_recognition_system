import { useEffect, useRef, useState } from 'react';
import { Activity, Camera, Check, Clock3, ScanFace, StopCircle, UserRound, Video } from 'lucide-react';
import { api, getApiError } from '../services/api';
import { useBrowserCamera } from '../hooks/useBrowserCamera';
import type { AttendanceEvent } from '../types';

interface AttendancePageProps {
  notify: (message: string, kind?: 'success' | 'error') => void;
}

interface FaceBox { top: number; right: number; bottom: number; left: number }

function timeLabel(value?: string | null) {
  return value ? new Date(value).toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—';
}

export default function AttendancePage({ notify }: AttendancePageProps) {
  const camera = useBrowserCamera();
  const [sessionId, setSessionId] = useState('');
  const [frameInterval, setFrameInterval] = useState(1200);
  const [boxes, setBoxes] = useState<FaceBox[]>([]);
  const [message, setMessage] = useState('Kamera ishga tushirilmagan.');
  const [lastEvent, setLastEvent] = useState<Record<string, unknown> | null>(null);
  const [events, setEvents] = useState<AttendanceEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const tickRef = useRef<number | undefined>(undefined);
  const busyRef = useRef(false);
  const sessionRef = useRef('');

  async function loadToday() {
    try { setEvents(await api.today()); } catch (error) { setMessage(getApiError(error)); }
  }
  useEffect(() => { void loadToday(); }, []);

  async function startCamera() {
    setLoading(true);
    try {
      const session = await api.startCamera();
      const opened = await camera.start();
      if (!opened) {
        await api.stopCamera(session.session_id).catch(() => undefined);
        return;
      }
      sessionRef.current = session.session_id;
      setSessionId(session.session_id);
      setFrameInterval(Math.max(700, session.frame_interval_ms));
      setMessage('Kamera tayyor. Yuz aniqlanishi kutilmoqda.');
      notify('Kamera ishga tushdi.');
    } catch (error) {
      setMessage(getApiError(error));
      notify(getApiError(error), 'error');
    } finally { setLoading(false); }
  }

  async function stopCamera() {
    camera.stop();
    const current = sessionRef.current;
    sessionRef.current = '';
    setSessionId('');
    setBoxes([]);
    setMessage('Kamera to‘xtatildi.');
    if (current) await api.stopCamera(current).catch(() => undefined);
  }

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      if (!cancelled && camera.active && sessionId && !busyRef.current) {
        busyRef.current = true;
        try {
          const frame = await camera.capture(0.7);
          if (frame) {
            const result = await api.recognize(sessionId, frame);
            if (!cancelled) {
              setBoxes((result.boxes as FaceBox[]) || []);
              setMessage(String(result.message || 'Kadr tekshirildi.'));
              if (['entry', 'exit'].includes(String(result.status))) {
                const event = result as Record<string, unknown>;
                setLastEvent(event);
                notify(String(result.message));
                await loadToday();
              } else if (result.status === 'unknown') {
                setLastEvent({ name: 'Xodim tanilmadi', timestamp: new Date().toISOString(), status: 'unknown' });
              }
            }
          }
        } catch (error) {
          if (!cancelled) {
            const detail = getApiError(error);
            setMessage(detail);
            if (!detail.includes('Takroriy')) notify(detail, 'error');
          }
        } finally { busyRef.current = false; }
      }
      if (!cancelled) tickRef.current = window.setTimeout(tick, frameInterval);
    };
    if (camera.active && sessionId) void tick();
    return () => {
      cancelled = true;
      if (tickRef.current) window.clearTimeout(tickRef.current);
    };
  }, [camera.active, sessionId, frameInterval]);

  useEffect(() => () => {
    camera.stop();
    if (sessionRef.current) void api.stopCamera(sessionRef.current).catch(() => undefined);
  }, []);

  const identity = lastEvent?.employee as Record<string, unknown> | undefined;
  const faceBoxes = boxes.map((box, index) => <div key={index} className="face-box" style={{ top: `${box.top * 100}%`, left: `${(1 - box.right) * 100}%`, width: `${(box.right - box.left) * 100}%`, height: `${(box.bottom - box.top) * 100}%` }} />);

  return <>
    <div className="page-heading"><div><div className="eyebrow">Jonli nazorat</div><h1>Davomat kamerasi</h1><p>Brauzer kamerasidan kadrlar belgilangan oraliqda serverga yuboriladi.</p></div><span className={`status-pill ${camera.active ? '' : 'inactive'}`}><span style={{ width: 6, height: 6, borderRadius: '50%', background: camera.active ? '#17865d' : '#c24143' }} />{camera.active ? 'Faol' : 'To‘xtagan'}</span></div>
    <div className="camera-layout">
      <section className="panel" style={{ padding: 14 }}>
        <div className="camera-stage">
          {camera.active ? <video ref={camera.videoRef} muted playsInline /> : <div className="camera-placeholder"><div><Video size={32} /><p>{camera.cameraError || 'Kamera tasviri uchun “Kamerani ishga tushirish” tugmasini bosing.'}</p></div></div>}
          {faceBoxes}
          {camera.active && <div style={{ position: 'absolute', left: 12, top: 12, padding: '5px 8px', color: 'white', background: 'rgba(10,20,34,.65)', borderRadius: 4, fontSize: 10 }}>● Jonli tasvir · {Math.round(1000 / frameInterval)} kadr/soniya</div>}
        </div>
        <div className="camera-controls">
          {!camera.active ? <button className="button primary" onClick={() => void startCamera()} disabled={loading}><Camera size={15} />{loading ? 'Ishga tushmoqda…' : 'Kamerani ishga tushirish'}</button> : <button className="button danger" onClick={() => void stopCamera()}><StopCircle size={15} /> Kamerani to‘xtatish</button>}
          <button className="button" onClick={() => void loadToday()}><Activity size={15} /> Hodisalarni yangilash</button>
        </div>
        <div className="person-secondary" style={{ marginTop: 11 }}>{message}</div>
      </section>
      <aside className="camera-side">
        <section className="panel"><div className="panel-head"><div><h2>Oxirgi aniqlangan xodim</h2><p>Serverdagi yuz taqqoslash natijasi</p></div><ScanFace size={16} color="#2563eb" /></div><div className="panel-body">
          {identity ? <div className="event-highlight"><strong>{String(identity.name || 'Xodim')}</strong><span>ID {String(identity.employee_code || identity.id || '—')} · {String(identity.department || 'Bo‘lim belgilanmagan')}</span><span>{lastEvent?.confidence != null ? `Ishonchlilik ${Number(lastEvent.confidence).toFixed(1)}%` : String(lastEvent?.message || '')}</span><span>{timeLabel(String(lastEvent?.timestamp || ''))}</span></div> : <div className="empty-state" style={{ padding: '22px 8px' }}><UserRound size={22} /><strong>Hali aniqlanmadi</strong><p>Kamera ishga tushgach natija chiqadi.</p></div>}
        </div></section>
        <section className="panel"><div className="panel-head"><div><h2>Bugungi hodisalar</h2><p>{events.length} ta xodim yozuvi</p></div><Clock3 size={15} color="#718096" /></div>
          {events.length ? <div className="table-wrap"><table><thead><tr><th>Xodim</th><th>Kirish</th><th>Chiqish</th></tr></thead><tbody>{events.slice(0, 12).map((event) => <tr key={event.employee_id}><td><span className="person-primary">{event.name}</span><span className="person-secondary">{event.employee_code || event.employee_id}</span></td><td>{timeLabel(event.entry_time)}</td><td>{timeLabel(event.exit_time)}</td></tr>)}</tbody></table></div> : <div className="empty-state" style={{ padding: '22px 8px' }}><Check size={20} /><strong>Hodisalar yo‘q</strong><p>Bugungi davomat shu yerda ko‘rinadi.</p></div>}
        </section>
      </aside>
    </div>
  </>;
}
