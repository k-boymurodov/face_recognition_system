export type Role = 'admin' | 'operator' | 'reports';

export interface User {
  id: number;
  username: string;
  role: Role;
}

export interface Employee {
  id: number;
  employee_code: string | null;
  name: string;
  department: string | null;
  position: string | null;
  phone: string | null;
  status: 'active' | 'inactive';
  created_at: string | null;
  face_registered_at?: string | null;
  has_face: boolean;
}

export interface AttendanceEvent {
  id?: number;
  employee_id: number;
  employee_code?: string;
  name: string;
  department: string | null;
  action?: 'entry' | 'exit';
  timestamp?: string;
  date?: string;
  entry_time?: string | null;
  exit_time?: string | null;
  status?: string;
  confidence?: number;
  work_minutes?: number | null;
}

export interface DashboardStats {
  date: string;
  total_employees: number;
  present: number;
  working: number;
  late: number;
  absent: number;
  entries: number;
  exits: number;
  weekly: { day: string; present: number }[];
  departments: { department: string; total: number }[];
  recent_events: AttendanceEvent[];
  today_employees: AttendanceEvent[];
}

export interface ApiError extends Error {
  status?: number;
}
