import type { DashboardStats, Employee, User } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const error = new Error(payload?.detail ?? `Server xatosi (${response.status})`) as Error & { status?: number };
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) => request<{ user: User }>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  me: () => request<{ user: User | null }>('/auth/me'),
  dashboard: (date?: string) => request<DashboardStats>(`/dashboard/stats${date ? `?report_date=${date}` : ''}`),
  employees: (query = '') => request<Employee[]>(`/employees${query ? `?q=${encodeURIComponent(query)}` : ''}`),
  employee: (id: number) => request<Employee>(`/employees/${id}`),
  createEmployee: (payload: Omit<Employee, 'id' | 'created_at' | 'has_face'>) => request<{ id: number; message: string }>('/employees', { method: 'POST', body: JSON.stringify(payload) }),
  updateEmployee: (id: number, payload: Partial<Employee>) => request<{ ok: boolean }>(`/employees/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteEmployee: (id: number) => request<{ ok: boolean }>(`/employees/${id}`, { method: 'DELETE' }),
  registerFace: (id: number, image: Blob) => {
    const data = new FormData();
    data.append('image', image, 'face.jpg');
    return request<{ ok: boolean; message: string }>(`/employees/${id}/register-face`, { method: 'POST', body: data });
  },
  inspectFace: (image: Blob) => {
    const data = new FormData();
    data.append('image', image, 'preview.jpg');
    return request<{ face_count: number; boxes: { top: number; right: number; bottom: number; left: number }[] }>('/face/inspect', { method: 'POST', body: data });
  },
  startCamera: () => request<{ session_id: string; frame_interval_ms: number }>('/attendance/camera-session/start', { method: 'POST' }),
  stopCamera: (sessionId: string) => request<{ ok: boolean }>('/attendance/camera-session/stop', { method: 'POST', body: JSON.stringify({ session_id: sessionId }) }),
  recognize: (sessionId: string, image: Blob) => {
    const data = new FormData();
    data.append('image', image, 'frame.jpg');
    return request<Record<string, unknown>>('/attendance/recognize', {
      method: 'POST',
      headers: { 'X-Camera-Session': sessionId },
      body: data,
    });
  },
  today: () => request<DashboardStats['today_employees']>('/attendance/today'),
  reports: (start: string, end: string) => request<DashboardStats['today_employees']>(`/attendance?start_date=${start}&end_date=${end}`),
  employeeHistory: (id: number) => request<Record<string, unknown>[]>(`/attendance/history/${id}`),
  exportUrl: (start: string, end: string) => `/api/reports/export?start_date=${start}&end_date=${end}`,
};

export function getApiError(error: unknown): string {
  return error instanceof Error ? error.message : 'Kutilmagan xatolik yuz berdi.';
}
