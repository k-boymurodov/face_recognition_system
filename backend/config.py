from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _csv_env(name: str, default: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


@dataclass(frozen=True)
class Settings:
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "bank_attendance")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_ttl_minutes: int = int(os.getenv("JWT_TTL_MINUTES", "480"))
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    cors_origins: tuple[str, ...] = tuple(_csv_env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"))
    admin_username: str = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    face_tolerance: float = float(os.getenv("FACE_TOLERANCE", "0.5"))
    frame_interval_ms: int = int(os.getenv("FRAME_INTERVAL_MS", "1200"))
    duplicate_cooldown_seconds: int = int(os.getenv("ATTENDANCE_COOLDOWN_SECONDS", "30"))
    shift_start_time: str = os.getenv("SHIFT_START_TIME", "09:00")
    working_days: tuple[int, ...] = tuple(
        int(day) for day in os.getenv("WORKING_DAYS", "0,1,2,3,4").split(",")
        if day.strip().isdigit() and 0 <= int(day) <= 6
    )


settings = Settings()
