from contextlib import asynccontextmanager
from csv import DictWriter
from datetime import date, datetime, time, timedelta
from io import StringIO
import logging
from threading import Lock
from time import monotonic
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import bcrypt
import mysql.connector
from mysql.connector import IntegrityError

from backend.auth import (
    COOKIE_NAME,
    authenticate,
    bootstrap_admin,
    clear_session,
    current_user,
    require_roles,
    read_session,
    set_session,
)
from backend.config import settings
from backend.database import DatabaseUnavailable, ensure_schema, healthcheck, transaction
from backend.face_service import analyze_image, find_duplicate, match_employee
from backend.schemas import EmployeeCreate, EmployeeUpdate, LoginRequest, UserCreate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("attendance.web")
TZ = ZoneInfo("Asia/Tashkent")
_sessions: dict[str, tuple[int, float, float]] = {}
_sessions_lock = Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        ensure_schema()
        bootstrap_admin()
        log.info("MySQL sxemasi tekshirildi; web API tayyor.")
    except Exception as exc:
        log.error("MySQL startup tekshiruvi bajarilmadi: %s", exc)
    yield


app = FastAPI(title="Bank Davomat API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Camera-Session"],
)


@app.exception_handler(DatabaseUnavailable)
async def database_error_handler(_: Request, exc: DatabaseUnavailable):
    message = str(exc)
    log.error("MySQL so'rovi bajarilmadi: %s", message)
    if "1524" in message or "mysql_native_password" in message:
        detail = "MySQL 1524: mysql_native_password serverda yoqilmagan. MySQL administratoridan caching_sha2_password hisobini sozlashni so'rang."
    else:
        detail = "MySQL bazasiga ulanib bo'lmadi. DB_HOST, DB_USER, DB_PASSWORD va DB_NAME qiymatlarini tekshiring."
    return JSONResponse(status_code=503, content={"detail": detail})


def _public_employee(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "employee_code": row.get("employee_code"),
        "name": row["name"],
        "department": row.get("department"),
        "position": row.get("position"),
        "phone": row.get("phone"),
        "status": row.get("status") or "active",
        "created_at": row.get("created_at"),
        "face_registered_at": row.get("face_registered_at"),
        "has_face": bool(row.get("face_encoding")),
    }


def _ensure_camera_session(session_id: str | None, user_id: int, enforce_interval: bool = False) -> None:
    if not session_id:
        raise HTTPException(status_code=400, detail="Kamera sessiyasi boshlanmagan.")
    now = monotonic()
    with _sessions_lock:
        session = _sessions.get(session_id)
        if not session or session[0] != user_id or session[1] < monotonic():
            _sessions.pop(session_id, None)
            raise HTTPException(status_code=409, detail="Kamera sessiyasi tugagan. Qayta boshlang.")
        interval = max(settings.frame_interval_ms, 500) / 1000
        if enforce_interval and now - session[2] < interval:
            raise HTTPException(status_code=429, detail="Kadrlar orasidagi minimal vaqt saqlansin.")
        last_frame = now if enforce_interval else session[2]
        _sessions[session_id] = (user_id, now + 1800, last_frame)


def _attendance_event(employee: dict, confidence: float) -> dict:
    now = datetime.now(TZ).replace(tzinfo=None, microsecond=0)
    today = now.date()
    with transaction() as (_, cursor):
        cursor.execute(
            "SELECT id FROM employees WHERE id = %s AND status = 'active' FOR UPDATE",
            (employee["id"],),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Xodim faol emas yoki topilmadi.")
        cursor.execute(
            """SELECT action, timestamp FROM attendance_log
               WHERE employee_id = %s AND DATE(timestamp) = %s
               ORDER BY id DESC LIMIT 1""",
            (employee["id"], today),
        )
        latest = cursor.fetchone()
        if latest:
            elapsed = (now - latest["timestamp"]).total_seconds()
            if elapsed < settings.duplicate_cooldown_seconds:
                return {
                    "status": "duplicate",
                    "message": "Takroriy hodisa qayd etilmadi.",
                    "employee": employee,
                    "cooldown_seconds": max(1, settings.duplicate_cooldown_seconds - int(elapsed)),
                }
            if latest["action"] == "exit":
                return {
                    "status": "complete",
                    "message": "Bugungi kirish-chiqish jufti allaqachon qayd etilgan.",
                    "employee": employee,
                }
            action = "exit"
        else:
            action = "entry"

        cursor.execute(
            "SELECT id, entry_time, exit_time FROM attendance WHERE employee_id = %s AND date = %s FOR UPDATE",
            (employee["id"], today),
        )
        daily = cursor.fetchone()
        if action == "entry":
            attendance_status = "late" if now.time() > time.fromisoformat(settings.shift_start_time) else "present"
            if daily is None:
                cursor.execute(
                    "INSERT INTO attendance (employee_id, entry_time, date, status) VALUES (%s, %s, %s, %s)",
                    (employee["id"], now, today, attendance_status),
                )
            elif daily["entry_time"] is None:
                cursor.execute("UPDATE attendance SET entry_time = %s, status = %s WHERE id = %s", (now, attendance_status, daily["id"]))
        else:
            if daily is None or daily["entry_time"] is None or daily["exit_time"] is not None:
                return {"status": "invalid", "message": "Bugungi davomat holati kirish-chiqishga mos emas.", "employee": employee}
            cursor.execute("UPDATE attendance SET exit_time = %s WHERE id = %s", (now, daily["id"]))

        cursor.execute(
            "INSERT INTO attendance_log (employee_id, timestamp, action, confidence) VALUES (%s, %s, %s, %s)",
            (employee["id"], now, action, confidence),
        )
        return {
            "status": action,
            "message": "Kirish qayd etildi." if action == "entry" else "Chiqish qayd etildi.",
            "employee": employee,
            "timestamp": now,
            "confidence": confidence,
        }


def _report_rows(start: date, end: date, employee_id: int | None = None, department: str | None = None):
    if (end - start).days > 366:
        raise HTTPException(status_code=422, detail="Hisobot oralig'i 367 kundan oshmasligi kerak.")
    employee_conditions = ["e.status = 'active'"]
    employee_params: list = []
    if employee_id is not None:
        employee_conditions.append("e.id = %s")
        employee_params.append(employee_id)
    if department:
        employee_conditions.append("e.department = %s")
        employee_params.append(department)
    with transaction() as (_, cursor):
        cursor.execute(
            "SELECT e.id, e.employee_code, e.name, e.department, e.position "
            "FROM employees e WHERE " + " AND ".join(employee_conditions) + " ORDER BY e.name",
            tuple(employee_params),
        )
        employees = cursor.fetchall()
        cursor.execute(
            """SELECT e.id, a.date, a.entry_time, a.exit_time, a.status,
                      CASE WHEN a.entry_time IS NOT NULL AND a.exit_time IS NOT NULL
                           THEN TIMESTAMPDIFF(MINUTE, a.entry_time, a.exit_time) ELSE NULL END AS work_minutes
               FROM attendance a JOIN employees e ON e.id = a.employee_id
               WHERE a.date BETWEEN %s AND %s AND e.status = 'active'""",
            (start, end),
        )
        attendance = {(row["id"], row["date"]): row for row in cursor.fetchall()}

    results = []
    day = start
    while day <= end:
        if day.weekday() in settings.working_days:
            for employee in employees:
                row = attendance.get((employee["id"], day))
                results.append({
                    **employee,
                    "date": day,
                    "entry_time": row["entry_time"] if row else None,
                    "exit_time": row["exit_time"] if row else None,
                    "status": row["status"] if row else "absent",
                    "work_minutes": row["work_minutes"] if row else None,
                })
        day += timedelta(days=1)
    return results


def _employee_exists(employee_id: int) -> bool:
    with transaction() as (_, cursor):
        cursor.execute("SELECT id FROM employees WHERE id = %s", (employee_id,))
        return cursor.fetchone() is not None


def _store_face(employee_id: int, encoding) -> None:
    registered_at = datetime.now(TZ).replace(tzinfo=None, microsecond=0)
    with transaction() as (_, cursor):
        cursor.execute(
            "UPDATE employees SET face_encoding = %s, face_registered_at = %s WHERE id = %s",
            (encoding.astype("float64").tobytes(), registered_at, employee_id),
        )


@app.get("/api/health")
def api_health():
    return healthcheck()


@app.post("/api/auth/login")
def login(payload: LoginRequest, request: Request, response: Response):
    client_key = request.client.host if request.client else "unknown"
    user = authenticate(payload.username, payload.password, client_key)
    set_session(response, user)
    return {"user": user}


@app.post("/api/auth/logout")
def logout(response: Response, _: dict = Depends(current_user)):
    clear_session(response)
    return {"ok": True}


@app.get("/api/auth/me")
def me(request: Request):
    return {"user": read_session(request.cookies.get(COOKIE_NAME))}


@app.get("/api/auth/users")
def list_users(_: dict = Depends(require_roles("admin"))):
    with transaction() as (_, cursor):
        cursor.execute("SELECT id, username, role, active, created_at FROM web_users ORDER BY username")
        return cursor.fetchall()


@app.post("/api/auth/users", status_code=201)
def create_user(payload: UserCreate, _: dict = Depends(require_roles("admin"))):
    password_hash = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    with transaction() as (_, cursor):
        try:
            cursor.execute(
                "INSERT INTO web_users (username, password_hash, role) VALUES (%s, %s, %s)",
                (payload.username, password_hash, payload.role),
            )
            user_id = cursor.lastrowid
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Bu login avval ro'yxatdan o'tgan.") from exc
    return {"id": int(user_id), "username": payload.username, "role": payload.role}


@app.get("/api/dashboard/stats")
def dashboard_stats(
    report_date: date | None = None,
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    today = report_date or datetime.now(TZ).date()
    week_start = today - timedelta(days=6)
    with transaction() as (_, cursor):
        cursor.execute("SELECT COUNT(*) AS total FROM employees WHERE status = 'active'")
        total = cursor.fetchone()["total"]
        cursor.execute(
             """SELECT SUM(CASE WHEN a.entry_time IS NOT NULL THEN 1 ELSE 0 END) AS present,
                 SUM(CASE WHEN a.entry_time IS NOT NULL AND a.exit_time IS NULL THEN 1 ELSE 0 END) AS working,
                 SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) AS late
             FROM attendance a JOIN employees e ON e.id = a.employee_id
             WHERE a.date = %s AND e.status = 'active'""",
            (today,),
        )
        counts = cursor.fetchone()
        cursor.execute(
            """SELECT SUM(CASE WHEN action = 'entry' THEN 1 ELSE 0 END) AS entries,
                      SUM(CASE WHEN action = 'exit' THEN 1 ELSE 0 END) AS exits
               FROM attendance_log WHERE DATE(timestamp) = %s""",
            (today,),
        )
        event_counts = cursor.fetchone()
        cursor.execute(
            """SELECT DATE(date) AS day, COUNT(*) AS present
               FROM attendance WHERE date BETWEEN %s AND %s AND entry_time IS NOT NULL
               GROUP BY DATE(date) ORDER BY day""",
            (week_start, today),
        )
        weekly = cursor.fetchall()
        cursor.execute(
            """SELECT COALESCE(NULLIF(department, ''), 'Belgilanmagan') AS department,
                      COUNT(*) AS total FROM employees WHERE status = 'active'
               GROUP BY department ORDER BY total DESC LIMIT 8"""
        )
        departments = cursor.fetchall()
        cursor.execute(
            """SELECT l.id, l.timestamp, l.action, l.confidence,
                      e.id AS employee_id, e.employee_code, e.name, e.department
               FROM attendance_log l JOIN employees e ON e.id = l.employee_id
               WHERE DATE(l.timestamp) = %s ORDER BY l.id DESC LIMIT 8""",
            (today,),
        )
        recent = cursor.fetchall()
        cursor.execute(
            """SELECT e.id, e.employee_code, e.name, e.department, a.entry_time, a.exit_time
               FROM employees e LEFT JOIN attendance a ON a.employee_id = e.id AND a.date = %s
               WHERE e.status = 'active' ORDER BY a.entry_time DESC, e.name LIMIT 100""",
            (today,),
        )
        daily = cursor.fetchall()
    present = int(counts["present"] or 0)
    return {
        "date": today,
        "total_employees": int(total),
        "present": present,
        "working": int(counts["working"] or 0),
        "late": int(counts["late"] or 0),
        "absent": max(0, int(total) - present) if today.weekday() in settings.working_days else 0,
        "entries": int(event_counts["entries"] or 0),
        "exits": int(event_counts["exits"] or 0),
        "weekly": weekly,
        "departments": departments,
        "recent_events": recent,
        "today_employees": daily,
    }


@app.get("/api/employees")
def list_employees(
    q: str = "",
    department: str | None = None,
    position: str | None = None,
    status_filter: str = Query(default="all", alias="status"),
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    conditions = []
    params: list = []
    if q.strip():
        term = f"%{q.strip()}%"
        conditions.append("(name LIKE %s OR employee_code LIKE %s OR department LIKE %s OR position LIKE %s)")
        params.extend([term] * 4)
    if department:
        conditions.append("department = %s")
        params.append(department)
    if position:
        conditions.append("position = %s")
        params.append(position)
    if status_filter in {"active", "inactive"}:
        conditions.append("status = %s")
        params.append(status_filter)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    with transaction() as (_, cursor):
        cursor.execute(
            "SELECT id, employee_code, name, department, position, phone, status, created_at, face_registered_at, face_encoding FROM employees" + where + " ORDER BY name",
            tuple(params),
        )
        rows = cursor.fetchall()
    return [_public_employee(row) for row in rows]


@app.post("/api/employees", status_code=201)
def create_employee(payload: EmployeeCreate, _: dict = Depends(require_roles("admin"))):
    with transaction() as (_, cursor):
        try:
            cursor.execute(
                """INSERT INTO employees (employee_code, name, department, position, phone, status, face_encoding)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (payload.employee_code, payload.name, payload.department, payload.position, payload.phone, payload.status, b""),
            )
            employee_id = cursor.lastrowid
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Xodim ID raqami yoki F.I.Sh. avval ro'yxatga olingan.") from exc
    return {"id": int(employee_id), "message": "Xodim yaratildi. Endi yuzini ro'yxatdan o'tkazing."}


@app.get("/api/employees/{employee_id}")
def get_employee(employee_id: int, _: dict = Depends(require_roles("admin", "operator", "reports"))):
    with transaction() as (_, cursor):
        cursor.execute(
            "SELECT id, employee_code, name, department, position, phone, status, created_at, face_registered_at, face_encoding FROM employees WHERE id = %s",
            (employee_id,),
        )
        row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Xodim topilmadi.")
    return _public_employee(row)


@app.put("/api/employees/{employee_id}")
def update_employee(employee_id: int, payload: EmployeeUpdate, _: dict = Depends(require_roles("admin"))):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="O'zgartirish uchun maydon berilmadi.")
    allowed = {"employee_code", "name", "department", "position", "phone", "status"}
    fields = [key for key in changes if key in allowed]
    sql = ", ".join(f"{field} = %s" for field in fields)
    with transaction() as (_, cursor):
        try:
            cursor.execute(f"UPDATE employees SET {sql} WHERE id = %s", tuple(changes[field] for field in fields) + (employee_id,))
            if cursor.rowcount == 0:
                cursor.execute("SELECT id FROM employees WHERE id = %s", (employee_id,))
                if cursor.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Xodim topilmadi.")
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Xodim ID raqami yoki F.I.Sh. band.") from exc
    return {"ok": True}


@app.delete("/api/employees/{employee_id}")
def delete_employee(employee_id: int, _: dict = Depends(require_roles("admin"))):
    with transaction() as (_, cursor):
        cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Xodim topilmadi.")
    return {"ok": True}


@app.post("/api/employees/{employee_id}/register-face")
async def register_face(
    employee_id: int,
    image: UploadFile = File(...),
    _: dict = Depends(require_roles("admin")),
):
    image_bytes = await image.read(5 * 1024 * 1024 + 1)
    try:
        result = await run_in_threadpool(analyze_image, image_bytes, True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not await run_in_threadpool(_employee_exists, employee_id):
        raise HTTPException(status_code=404, detail="Xodim topilmadi.")
    duplicate = await run_in_threadpool(find_duplicate, result.encoding, employee_id)
    if duplicate:
        raise HTTPException(status_code=409, detail="Bu yuz boshqa xodim uchun ro'yxatdan o'tgan.")
    await run_in_threadpool(_store_face, employee_id, result.encoding)
    return {"ok": True, "message": "Xodim muvaffaqiyatli ro'yxatdan o'tkazildi.", "face_count": 1}


@app.post("/api/face/inspect")
async def inspect_face(
    image: UploadFile = File(...),
    _: dict = Depends(require_roles("admin", "operator")),
):
    try:
        result = await run_in_threadpool(analyze_image, await image.read(5 * 1024 * 1024 + 1))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"face_count": len(result.boxes), "boxes": result.boxes}


@app.post("/api/attendance/camera-session/start")
def start_camera_session(user: dict = Depends(require_roles("admin", "operator"))):
    session_id = str(uuid4())
    with _sessions_lock:
        _sessions[session_id] = (user["id"], monotonic() + 1800, 0.0)
    return {"session_id": session_id, "frame_interval_ms": settings.frame_interval_ms}


@app.post("/api/attendance/camera-session/stop")
def stop_camera_session(payload: dict, user: dict = Depends(require_roles("admin", "operator"))):
    session_id = payload.get("session_id")
    with _sessions_lock:
        session = _sessions.get(session_id)
        if session and session[0] == user["id"]:
            _sessions.pop(session_id, None)
    return {"ok": True}


@app.post("/api/attendance/recognize")
async def recognize_attendance(
    request: Request,
    image: UploadFile = File(...),
    user: dict = Depends(require_roles("admin", "operator")),
):
    _ensure_camera_session(request.headers.get("X-Camera-Session"), user["id"], enforce_interval=True)
    try:
        result = await run_in_threadpool(analyze_image, await image.read(5 * 1024 * 1024 + 1), True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    employee = await run_in_threadpool(match_employee, result.encoding)
    if employee is None:
        return {"status": "unknown", "message": "Xodim tanilmadi.", "boxes": result.boxes}
    event = await run_in_threadpool(_attendance_event, employee, employee["confidence"])
    return {**event, "boxes": result.boxes}


@app.get("/api/attendance/today")
def attendance_today(_: dict = Depends(require_roles("admin", "operator", "reports"))):
    today = datetime.now(TZ).date()
    with transaction() as (_, cursor):
        cursor.execute(
            """SELECT e.id, e.employee_code, e.name, e.department, e.position,
                      a.entry_time, a.exit_time, a.status
               FROM employees e LEFT JOIN attendance a ON a.employee_id = e.id AND a.date = %s
               WHERE e.status = 'active' ORDER BY a.entry_time DESC, e.name""",
            (today,),
        )
        return cursor.fetchall()


@app.get("/api/attendance")
def attendance_list(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: int | None = None,
    department: str | None = None,
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    end = end_date or datetime.now(TZ).date()
    start = start_date or end
    if start > end:
        raise HTTPException(status_code=422, detail="Boshlanish sanasi tugash sanasidan keyin bo'lmasin.")
    return _report_rows(start, end, employee_id, department)


@app.get("/api/attendance/history/{employee_id}")
def attendance_history(
    employee_id: int,
    days: int = Query(default=30, ge=1, le=365),
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    start = datetime.now(TZ).date() - timedelta(days=days - 1)
    with transaction() as (_, cursor):
        cursor.execute("SELECT id FROM employees WHERE id = %s", (employee_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Xodim topilmadi.")
        cursor.execute(
            """SELECT id, timestamp, action, confidence FROM attendance_log
               WHERE employee_id = %s AND timestamp >= %s ORDER BY timestamp DESC""",
            (employee_id, datetime.combine(start, time.min)),
        )
        return cursor.fetchall()


@app.get("/api/reports/daily")
def report_daily(
    report_date: date | None = None,
    employee_id: int | None = None,
    department: str | None = None,
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    day = report_date or datetime.now(TZ).date()
    return _report_rows(day, day, employee_id, department)


@app.get("/api/reports/weekly")
def report_weekly(
    end_date: date | None = None,
    employee_id: int | None = None,
    department: str | None = None,
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    end = end_date or datetime.now(TZ).date()
    return _report_rows(end - timedelta(days=6), end, employee_id, department)


@app.get("/api/reports/monthly")
def report_monthly(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    employee_id: int | None = None,
    department: str | None = None,
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    today = datetime.now(TZ).date()
    year = year or today.year
    month = month or today.month
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return _report_rows(start, end, employee_id, department)


@app.get("/api/reports/export")
def report_export(
    start_date: date,
    end_date: date,
    employee_id: int | None = None,
    department: str | None = None,
    _: dict = Depends(require_roles("admin", "operator", "reports")),
):
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="Sana oralig'i noto'g'ri.")
    rows = _report_rows(start_date, end_date, employee_id, department)
    output = StringIO()
    fields = ["id", "employee_code", "name", "department", "position", "date", "entry_time", "exit_time", "status", "work_minutes"]
    writer = DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        iter(["\ufeff" + output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=attendance-{start_date}-{end_date}.csv"},
    )
