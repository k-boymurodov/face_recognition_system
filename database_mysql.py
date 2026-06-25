import mysql.connector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'bank_attendance')
}


def get_connection():
    """MySQL bazaga ulanish."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Baza xatosi: {err}")
        return None


def create_tables():
    """Bazada jadvallar yaratish."""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                face_encoding LONGBLOB NOT NULL,
                department VARCHAR(50),
                position VARCHAR(50),
                status ENUM('active', 'inactive') DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                entry_time DATETIME,
                exit_time DATETIME,
                date DATE,
                status ENUM('present', 'absent', 'late') DEFAULT 'present',
                notes VARCHAR(255),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                INDEX idx_date (date),
                INDEX idx_employee_date (employee_id, date)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action ENUM('entry', 'exit') NOT NULL,
                confidence FLOAT,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                INDEX idx_timestamp (timestamp),
                INDEX idx_employee (employee_id)
            )
        """)
        
        conn.commit()
        print("✅ Bazaning jadvallari muvaffaqiyatli yaratildi!")
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Jadval yaratish xatosi: {err}")
        return False
    finally:
        cursor.close()
        conn.close()


def add_employee(name, face_encoding, department="", position=""):
    """Yangi xodim qo'shish."""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO employees (name, face_encoding, department, position)
            VALUES (%s, %s, %s, %s)
        """, (name, face_encoding, department, position))
        
        conn.commit()
        employee_id = cursor.lastrowid
        print(f"✅ {name} xodim qo'shildi (ID: {employee_id})")
        return employee_id
        
    except mysql.connector.Error as err:
        if "Duplicate entry" in str(err):
            print(f"⚠️ {name} allaqachon ro'yxatga olingan!")
        else:
            print(f"❌ Xodim qo'shish xatosi: {err}")
        return False
    finally:
        cursor.close()
        conn.close()


def record_attendance(employee_id, action='entry', confidence=0.0):
    """Davomat qaydini yozish (kelib ketish)."""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        today = datetime.now().date()
        
        cursor.execute("""
            INSERT INTO attendance_log (employee_id, action, confidence)
            VALUES (%s, %s, %s)
        """, (employee_id, action, confidence))
        
        if action == 'entry':
            cursor.execute("""
                INSERT INTO attendance (employee_id, entry_time, date, status)
                VALUES (%s, NOW(), %s, 'present')
                ON DUPLICATE KEY UPDATE entry_time = NOW()
            """, (employee_id, today))
        
        elif action == 'exit':
            cursor.execute("""
                UPDATE attendance
                SET exit_time = NOW()
                WHERE employee_id = %s AND date = %s AND exit_time IS NULL
            """, (employee_id, today))
        
        conn.commit()
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Davomat qaydiy xatosi: {err}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_employee_by_name(name):
    """Ism bo'yicha xodimni topish."""
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, name, face_encoding, department, position
            FROM employees
            WHERE name = %s AND status = 'active'
        """, (name,))
        
        result = cursor.fetchone()
        return result
        
    except mysql.connector.Error as err:
        print(f"❌ Xodim qidiruv xatosi: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_all_employees():
    """Barcha faol xodimlarni olish."""
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, name, face_encoding, department, position
            FROM employees
            WHERE status = 'active'
        """)
        
        results = cursor.fetchall()
        return results
        
    except mysql.connector.Error as err:
        print(f"❌ Xodimlarni olish xatosi: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_daily_attendance(date=None):
    """Kunlik davomat hisobi."""
    if not date:
        date = datetime.now().date()
    
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                e.id, e.name, e.department, e.position,
                a.entry_time, a.exit_time, a.status
            FROM employees e
            LEFT JOIN attendance a ON e.id = a.employee_id AND a.date = %s
            WHERE e.status = 'active'
            ORDER BY a.entry_time DESC
        """, (date,))
        
        results = cursor.fetchall()
        return results
        
    except mysql.connector.Error as err:
        print(f"❌ Davomat hisobi xatosi: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_attendance_report(start_date=None, end_date=None):
    """Haftalik/oylik davomat hisobi."""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).date()
    if not end_date:
        end_date = datetime.now().date()
    
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                e.name, e.department,
                COUNT(DISTINCT a.date) as kam_kunlar,
                COUNT(CASE WHEN a.entry_time IS NOT NULL THEN 1 END) as keldi,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as kech_keldi,
                AVG(TIMESTAMPDIFF(HOUR, a.entry_time, a.exit_time)) as orta_vaqt
            FROM employees e
            LEFT JOIN attendance a ON e.id = a.employee_id 
                AND a.date BETWEEN %s AND %s
            WHERE e.status = 'active'
            GROUP BY e.id, e.name, e.department
            ORDER BY e.name
        """, (start_date, end_date))
        
        results = cursor.fetchall()
        return results
        
    except mysql.connector.Error as err:
        print(f"❌ Hisobi xatosi: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_attendance_log(employee_id, days=7):
    """Xodimning so'nggi kelib ketishlari."""
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        cursor.execute("""
            SELECT timestamp, action, confidence
            FROM attendance_log
            WHERE employee_id = %s AND DATE(timestamp) >= %s
            ORDER BY timestamp DESC
        """, (employee_id, start_date))
        
        results = cursor.fetchall()
        return results
        
    except mysql.connector.Error as err:
        print(f"❌ Logni olish xatosi: {err}")
        return []
    finally:
        cursor.close()
        conn.close()
