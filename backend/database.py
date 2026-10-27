from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector

from backend.config import settings


class DatabaseUnavailable(RuntimeError):
    pass


def connect():
    connection = mysql.connector.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        connection_timeout=5,
        autocommit=False,
    )
    with connection.cursor() as cursor:
        cursor.execute("SET time_zone = '+05:00'")
    return connection


@contextmanager
def transaction() -> Iterator[tuple[Any, Any]]:
    connection = None
    try:
        connection = connect()
        cursor = connection.cursor(dictionary=True)
        yield connection, cursor
        connection.commit()
    except mysql.connector.Error as exc:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise DatabaseUnavailable(str(exc)) from exc
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        """SELECT 1 FROM information_schema.columns
           WHERE table_schema = %s AND table_name = %s AND column_name = %s""",
        (settings.db_name, table, column),
    )
    return cursor.fetchone() is not None


def _index_exists(cursor, table: str, index: str) -> bool:
    cursor.execute(
        """SELECT 1 FROM information_schema.statistics
           WHERE table_schema = %s AND table_name = %s AND index_name = %s""",
        (settings.db_name, table, index),
    )
    return cursor.fetchone() is not None


def ensure_schema() -> None:
    """Create missing web tables and add nullable employee fields without replacing legacy data."""
    with transaction() as (_, cursor):
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                face_encoding LONGBLOB NOT NULL,
                department VARCHAR(50),
                position VARCHAR(50),
                status ENUM('active', 'inactive') DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                entry_time DATETIME,
                exit_time DATETIME,
                date DATE,
                status ENUM('present', 'absent', 'late') DEFAULT 'present',
                notes VARCHAR(255),
                CONSTRAINT fk_attendance_employee FOREIGN KEY (employee_id)
                    REFERENCES employees(id) ON DELETE CASCADE,
                INDEX idx_date (date),
                INDEX idx_employee_date (employee_id, date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS attendance_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action ENUM('entry', 'exit') NOT NULL,
                confidence FLOAT,
                CONSTRAINT fk_attendance_log_employee FOREIGN KEY (employee_id)
                    REFERENCES employees(id) ON DELETE CASCADE,
                INDEX idx_timestamp (timestamp),
                INDEX idx_employee (employee_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS unknown_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                image LONGBLOB,
                camera_id VARCHAR(50),
                INDEX idx_timestamp_unknown (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS web_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'operator', 'reports') NOT NULL DEFAULT 'reports',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )

        if not _column_exists(cursor, "employees", "employee_code"):
            cursor.execute("ALTER TABLE employees ADD COLUMN employee_code VARCHAR(64) NULL")
        if not _column_exists(cursor, "employees", "phone"):
            cursor.execute("ALTER TABLE employees ADD COLUMN phone VARCHAR(32) NULL")
        if not _column_exists(cursor, "employees", "face_registered_at"):
            cursor.execute("ALTER TABLE employees ADD COLUMN face_registered_at DATETIME NULL")
        if not _index_exists(cursor, "employees", "uq_employee_code"):
            cursor.execute(
                "CREATE UNIQUE INDEX uq_employee_code ON employees (employee_code)"
            )

        if not _index_exists(cursor, "attendance", "uq_attendance_employee_date"):
            cursor.execute(
                """SELECT employee_id, date FROM attendance
                   GROUP BY employee_id, date HAVING COUNT(*) > 1 LIMIT 1"""
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "CREATE UNIQUE INDEX uq_attendance_employee_date ON attendance (employee_id, date)"
                )


def healthcheck() -> dict[str, str]:
    with transaction() as (_, cursor):
        cursor.execute("SELECT VERSION() AS version")
        row = cursor.fetchone()
        return {"status": "ok", "mysql_version": str(row["version"])}
