import sqlite3
import pickle
from datetime import datetime, timedelta
import logging
import contextlib
import csv
from pathlib import Path

DB_FILE = Path(__file__).with_name("bank_attendance.db")


def parse_datetime(value):
    """SQLite'dan kelgan vaqt matnini datetime obyektiga aylantirish."""
    if value is None or isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def row_to_dict(row, datetime_fields=None):
    """SQLite Row natijasini dict qilib, vaqt maydonlarini tayyorlash."""
    data = dict(row)
    for field in datetime_fields or ():
        data[field] = parse_datetime(data.get(field))
    return data

def get_connection():
    """SQLite bazaga ulanish (eski usul, endi context manager ishlatiladi)."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as err:
        logging.error(f"Baza ulanish xatosi: {err}")
        return None

@contextlib.contextmanager
def db_connect():
    """SQLite bazaga ulanish uchun context manager."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as err:
        logging.error(f"Baza ulanish xatosi: {err}")
        yield None
    finally:
        if conn:
            conn.close()

def create_tables():
    """SQLite jadvallari yaratish."""
    with db_connect() as conn:
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    face_encoding BLOB NOT NULL,
                    department TEXT,
                    position TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    entry_time DATETIME,
                    exit_time DATETIME,
                    date DATE,
                    status TEXT DEFAULT 'present',
                    notes TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action TEXT NOT NULL,
                    confidence REAL,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON attendance(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_date ON attendance(employee_id, date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON attendance_log(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee ON attendance_log(employee_id)")
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_employee_date_unique
                ON attendance(employee_id, date)
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unknown_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    image BLOB,
                    camera_id TEXT
                )
            """)
            
            conn.commit()
            logging.info("Bazaning jadvallari muvaffaqiyatli yaratildi!")
            return True
            
        except sqlite3.Error as err:
            logging.error(f"Jadval yaratish xatosi: {err}")
            return False
        finally:
            cursor.close()


def add_employee(name, face_encoding, department="", position=""):
    """Yangi xodim qo'shish."""
    with db_connect() as conn:
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # Xavfsizlik uchun pickle o'rniga to'g'ridan-to'g'ri numpy arrayni saqlaymiz
            face_encoding_bytes = face_encoding.tobytes()
            
            cursor.execute("""
                INSERT INTO employees (name, face_encoding, department, position)
                VALUES (?, ?, ?, ?)
            """, (name, face_encoding_bytes, department, position))
            
            conn.commit()
            employee_id = cursor.lastrowid
            logging.info(f"✅ {name} xodim qo'shildi (ID: {employee_id})")
            return employee_id
            
        except sqlite3.Error as err:
            if "UNIQUE constraint failed" in str(err):
                logging.warning(f"⚠️ {name} allaqachon ro'yxatga olingan!")
            else:
                logging.error(f"Xodim qo'shish xatosi: {err}")
            return False
        finally:
            cursor.close()


def record_attendance(employee_id, action='entry', confidence=0.0):
    """Davomat qaydini yozish."""
    with db_connect() as conn:
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            now = datetime.now().replace(microsecond=0)
            
            cursor.execute("""
                INSERT INTO attendance_log (employee_id, timestamp, action, confidence)
                VALUES (?, ?, ?, ?)
            """, (employee_id, now, action, confidence))
            
            if action == 'entry':
                cursor.execute("""
                    INSERT INTO attendance (employee_id, entry_time, date, status)
                    VALUES (?, ?, ?, 'present')
                    ON CONFLICT(employee_id, date) DO UPDATE SET
                        entry_time = COALESCE(attendance.entry_time, excluded.entry_time),
                        status = 'present'
                """, (employee_id, now, today))
            
            elif action == 'exit':
                cursor.execute("""
                    UPDATE attendance
                    SET exit_time = ?
                    WHERE employee_id = ? AND date = ?
                """, (now, employee_id, today))
            
            conn.commit()
            return True
            
        except sqlite3.Error as err:
            logging.error(f"Davomat qaydiy xatosi: {err}")
            return False
        finally:
            cursor.close()


def get_employee_by_name(name):
    """Ism bo'yicha xodimni topish."""
    with db_connect() as conn:
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, face_encoding, department, position
                FROM employees
                WHERE name = ? AND status = 'active'
            """, (name,))
            
            result = cursor.fetchone()
            return row_to_dict(result) if result else None
            
        except sqlite3.Error as err:
            logging.error(f"Xodim qidiruv xatosi: {err}")
            return None
        finally:
            cursor.close()


def get_all_employees():
    """Barcha faol xodimlarni olish."""
    with db_connect() as conn:
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, face_encoding, department, position
                FROM employees
                WHERE status = 'active'
            """)
            
            results = [row_to_dict(row) for row in cursor.fetchall()]
            return results
            
        except sqlite3.Error as err:
            logging.error(f"Xodimlarni olish xatosi: {err}")
            return []
        finally:
            cursor.close()


def get_daily_attendance(date=None):
    """Kunlik davomat hisobi."""
    if not date:
        date = datetime.now().date()
    
    with db_connect() as conn:
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    e.id, e.name, e.department, e.position,
                    a.entry_time, a.exit_time, a.status,
                    CAST((julianday(a.exit_time) - julianday(a.entry_time)) * 24 AS REAL) as work_hours
                FROM employees e
                LEFT JOIN attendance a ON e.id = a.employee_id AND a.date = ?
                WHERE e.status = 'active'
                ORDER BY a.entry_time DESC
            """, (date,))
            
            results = [
                row_to_dict(row, datetime_fields=("entry_time", "exit_time",))
                for row in cursor.fetchall()
            ]
            return results
            
        except sqlite3.Error as err:
            logging.error(f"Davomat hisobi xatosi: {err}")
            return []
        finally:
            cursor.close()


def get_attendance_report(start_date=None, end_date=None):
    """Haftalik/oylik davomat hisobi."""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).date()
    if not end_date:
        end_date = datetime.now().date()
    
    with db_connect() as conn:
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    e.name, e.department,
                    COUNT(DISTINCT a.date) as kam_kunlar,
                    COUNT(CASE WHEN a.entry_time IS NOT NULL THEN 1 END) as keldi,
                    COUNT(CASE WHEN a.status = 'late' THEN 1 END) as kech_keldi,
                    AVG(CAST((julianday(a.exit_time) - julianday(a.entry_time)) * 24 AS REAL)) as orta_vaqt
                FROM employees e
                LEFT JOIN attendance a ON e.id = a.employee_id 
                    AND a.date BETWEEN ? AND ?
                WHERE e.status = 'active'
                GROUP BY e.id, e.name, e.department
                ORDER BY e.name
            """, (start_date, end_date))
            
            results = [row_to_dict(row) for row in cursor.fetchall()]
            return results
            
        except sqlite3.Error as err:
            logging.error(f"Hisobi xatosi: {err}")
            return []
        finally:
            cursor.close()


def get_attendance_log(employee_id, days=7):
    """Xodimning so'nggi kelib ketishlari."""
    with db_connect() as conn:
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        try:
            start_date = (datetime.now() - timedelta(days=days)).date()
            
            cursor.execute("""
                SELECT timestamp, action, confidence
                FROM attendance_log
                WHERE employee_id = ? AND DATE(timestamp) >= ?
                ORDER BY timestamp DESC
            """, (employee_id, start_date))
            
            results = [
                row_to_dict(row, datetime_fields=("timestamp",))
                for row in cursor.fetchall()
            ]
            return results
            
        except sqlite3.Error as err:
            logging.error(f"Logni olish xatosi: {err}")
            return []
        finally:
            cursor.close()


def get_next_attendance_action(employee_id):
    """Bugungi holatga qarab keyingi harakatni aniqlash."""
    with db_connect() as conn:
        if not conn:
            return "entry"

        cursor = conn.cursor()

        try:
            today = datetime.now().strftime('%Y-%m-%d')
            # Bugungi oxirgi amalni logdan tekshiramiz (kelish/ketish navbatma-navbat bo'lishi uchun)
            cursor.execute("""
                SELECT action FROM attendance_log 
                WHERE employee_id = ? AND DATE(timestamp) = ?
                ORDER BY id DESC LIMIT 1
            """, (employee_id, today))

            record = cursor.fetchone()
            if not record:
                return "entry"
            
            # Agar oxirgisi entry bo'lsa, keyingisi exit bo'ladi va aksincha
            return "exit" if record["action"] == "entry" else "entry"

        except sqlite3.Error as err:
            logging.error(f"Davomat holati xatosi: {err}")
            return "entry"

def log_unknown_person(image_bytes, camera_id=None):
    """Noma'lum shaxs aniqlanganini bazaga yozish."""
    with db_connect() as conn:
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO unknown_events (image, camera_id)
                VALUES (?, ?)
            """, (image_bytes, camera_id))
            
            conn.commit()
            logging.info("⚠️ Noma'lum shaxs aniqlangani bazaga yozildi.")
            return True
            
        except sqlite3.Error as err:
            logging.error(f"Noma'lum shaxsni bazaga yozishda xato: {err}")
            return False
        finally:
            cursor.close()

def export_monthly_report_to_csv(year, month):
    """Oylik davomatni Excel (CSV) fayliga eksport qilish."""
    start_date = f"{year}-{month:02d}-01"
    
    # Keyingi oyning birinchi kunidan bitta oldingi kunni topish (oy oxiri)
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    filename = f"davomat_hisoboti_{year}_{month:02d}.csv"
    
    with db_connect() as conn:
        if conn is None:
            return None
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    e.name as 'Xodim',
                    e.department as 'Boʻlim',
                    a.date as 'Sana',
                    a.entry_time as 'Kelish',
                    a.exit_time as 'Ketish',
                    a.status as 'Holat'
                FROM employees e
                JOIN attendance a ON e.id = a.employee_id
                WHERE a.date >= ? AND a.date < ?
                ORDER BY a.date ASC, e.name ASC
            """, (start_date, end_date))
            
            rows = cursor.fetchall()
            if not rows:
                return False # Ma'lumot yo'q
            
            # Excel uchun UTF-8-SIG kodirovkasi bilan yozish
            with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # Sarlavhalar
                writer.writerow(['Xodim ismi', 'Boʻlim', 'Sana', 'Kelish vaqti', 'Ketish vaqti', 'Holati'])
                
                for row in rows:
                    writer.writerow([
                        row['Xodim'], row['Boʻlim'], row['Sana'],
                        row['Kelish'] if row['Kelish'] else "-",
                        row['Ketish'] if row['Ketish'] else "-",
                        row['Holat']
                    ])
            return filename
        except Exception as e:
            logging.error(f"Eksport xatosi: {e}")
            return None
        finally:
            cursor.close()
