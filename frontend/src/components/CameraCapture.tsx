import { useEffect, useRef, useState } from 'react';
import { Camera, Check, LoaderCircle, ScanFace, ShieldCheck, X } from 'lucide-react';
import { api, getApiError } from '../services/api';
import { useBrowserCamera } from '../hooks/useBrowserCamera';

interface CameraCaptureProps {
  employeeId: number;
  onComplete: (message: string) => void;
  onCancel: () => void;
}

interface FaceBox {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export default function CameraCapture({ employeeId, onComplete, onCancel }: CameraCaptureProps) {
  const camera = useBrowserCamera();
  const [boxes, setBoxes] = useState<FaceBox[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('Kamerani ochib, yuzingizni ramka ichiga joylashtiring.');
  const loopRef = useRef<number | undefined>(undefined);
  const inspectBusyRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    const inspect = async () => {
      if (!cancelled && camera.active && !inspectBusyRef.current) {
        inspectBusyRef.current = true;
        try {
          const blob = await camera.capture(0.68);
          if (blob) {
            const result = await api.inspectFace(blob);
            if (!cancelled) {
              setBoxes(result.boxes);
              setStatus(result.face_count === 1 ? 'Bitta yuz aniqlandi. Suratga olish mumkin.' : result.face_count > 1 ? 'Kadrda faqat bitta odam bo‘lishi kerak.' : 'Yuz topilmadi. Yorug‘roq joyga o‘ting.');
            }
          }
        } catch (error) {
          if (!cancelled) setStatus(getApiError(error));
        } finally {
          inspectBusyRef.current = false;
        }
      }
      if (!cancelled) loopRef.current = window.setTimeout(inspect, 1500);
    };
    if (camera.active) void inspect();
    return () => {
      cancelled = true;
      if (loopRef.current) window.clearTimeout(loopRef.current);
    };
  }, [camera.active]);

  async function saveFace() {
    setBusy(true);
    try {
      const blob = await camera.capture();
      if (!blob) throw new Error('Kameradan kadr olinmadi.');
      const result = await api.registerFace(employeeId, blob);
      camera.stop();
      onComplete(result.message);
    } catch (error) {
      setStatus(getApiError(error));
    } finally {
      setBusy(false);
    }
  }

  async function close() {
    camera.stop();
    onCancel();
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="camera-title">
        <div className="modal-head">
          <div><h2 id="camera-title">Yuzni ro‘yxatdan o‘tkazish</h2><p>Biometrik kod faqat serverda hisoblanadi va MySQL’da saqlanadi.</p></div>
          <button className="icon-button" onClick={close} aria-label="Yopish"><X size={16} /></button>
        </div>
        <div className="modal-body">
          <div className="camera-layout">
            <div>
              <div className="camera-stage">
                {camera.active ? <video ref={camera.videoRef} muted playsInline /> : <div className="camera-placeholder"><div><Camera size={30} /><p>Kamera tasviri shu yerda ko‘rinadi</p></div></div>}
                {boxes.map((box, index) => <div key={index} className="face-box" style={{ top: `${box.top * 100}%`, left: `${(1 - box.right) * 100}%`, width: `${(box.right - box.left) * 100}%`, height: `${(box.bottom - box.top) * 100}%` }} />)}
              </div>
              {camera.cameraError && <div className="error-banner" style={{ marginTop: 10 }}>{camera.cameraError}</div>}
              <div className="camera-controls">
                {!camera.active ? <button className="button primary" onClick={() => void camera.start()}><Camera size={15} /> Kamerani ochish</button> : <button className="button" onClick={camera.stop}><X size={15} /> Kamerani to‘xtatish</button>}
                <button className="button primary" onClick={() => void saveFace()} disabled={!camera.active || busy || boxes.length !== 1}><ScanFace size={15} />{busy ? 'Tekshirilmoqda…' : 'Yuzni saqlash'}</button>
              </div>
            </div>
            <aside className="camera-side">
              <div className="camera-note"><h3><ShieldCheck size={14} /> Kamera bo‘yicha</h3><ul><li>Yuzni yaxshi yoritilgan joyda tuting.</li><li>Kamera tomonga to‘g‘ri qarang.</li><li>Ko‘zoynak yoki niqob yuzni yopmasin.</li><li>Bu tekshiruv jonli odam ekanini kafolatlamaydi.</li></ul></div>
              <div className="event-highlight"><strong>{boxes.length === 1 ? 'Yuz ko‘rindi' : 'Kutilmoqda'}</strong><span>{status}</span></div>
              {busy && <p className="person-secondary"><LoaderCircle size={13} /> Yuz modeli tekshirilmoqda…</p>}
              {!busy && boxes.length === 1 && <p className="person-secondary"><Check size={13} /> Surat serverga vaqtincha yuboriladi.</p>}
            </aside>
          </div>
        </div>
      </section>
    </div>
  );
}
