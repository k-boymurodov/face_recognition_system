from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic
from typing import Any, Callable

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool

from backend.config import settings
from backend.database import transaction

COOKIE_NAME = "attendance_session"
_attempts: dict[str, tuple[int, float]] = {}
_attempts_lock = Lock()

# Foydalanuvchi topilmasa ham bcrypt tekshiruvi bajariladi (vaqt bo'yicha login aniqlanmasligi uchun).
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


def bootstrap_admin() -> None:
    if not settings.admin_password:
        return
    with transaction() as (_, cursor):
        cursor.execute("SELECT id FROM web_users WHERE username = %s", (settings.admin_username,))
        if cursor.fetchone() is not None:
            return
        password_hash = bcrypt.hashpw(
            settings.admin_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("ascii")
        cursor.execute(
            "INSERT INTO web_users (username, password_hash, role) VALUES (%s, %s, 'admin')",
            (settings.admin_username, password_hash),
        )


def _check_rate_limit(client_key: str) -> None:
    now = monotonic()
    with _attempts_lock:
        failures, blocked_until = _attempts.get(client_key, (0, 0.0))
        if blocked_until > now:
            raise HTTPException(status_code=429, detail="Juda ko'p urinish. Birozdan keyin urinib ko'ring.")
        if blocked_until:
            _attempts.pop(client_key, None)


def _record_failure(client_key: str) -> None:
    now = monotonic()
    with _attempts_lock:
        failures, _ = _attempts.get(client_key, (0, 0.0))
        failures += 1
        _attempts[client_key] = (failures, now + 900 if failures >= 5 else 0.0)


def authenticate(username: str, password: str, client_key: str) -> dict[str, Any]:
    _check_rate_limit(client_key)
    try:
        with transaction() as (_, cursor):
            cursor.execute(
                "SELECT id, username, password_hash, role FROM web_users WHERE username = %s AND active = TRUE",
                (username,),
            )
            user = cursor.fetchone()
    except Exception as exc:
        message = str(exc)
        if "1524" in message or "mysql_native_password" in message:
            detail = "MySQL 1524: mysql_native_password serverda yoqilmagan. MySQL administratoridan caching_sha2_password hisobini sozlashni so'rang."
        else:
            detail = "MySQL bazasiga ulanib bo'lmadi. DB_HOST, DB_USER, DB_PASSWORD va DB_NAME qiymatlarini tekshiring."
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from exc

    hash_bytes = user["password_hash"].encode("ascii") if user else _DUMMY_HASH
    try:
        valid = bcrypt.checkpw(password.encode("utf-8"), hash_bytes) and user is not None
    except (ValueError, TypeError):
        valid = False
    if not valid:
        _record_failure(client_key)
        raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri.")

    with _attempts_lock:
        _attempts.pop(client_key, None)
    return {"id": int(user["id"]), "username": user["username"], "role": user["role"]}


def set_session(response: Response, user: dict[str, Any]) -> None:
    if not settings.jwt_secret:
        raise HTTPException(status_code=503, detail="JWT_SECRET .env faylida sozlanmagan.")
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_ttl_minutes)
    token = jwt.encode(
        {"sub": str(user["id"]), "username": user["username"], "role": user["role"], "exp": expires},
        settings.jwt_secret,
        algorithm="HS256",
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.jwt_ttl_minutes * 60,
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="strict")


def read_session(token: str | None) -> dict[str, Any] | None:
    if not token or not settings.jwt_secret:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        return {
            "id": int(payload["sub"]),
            "username": payload["username"],
            "role": payload["role"],
        }
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return None


def _load_active_user(user_id: int) -> dict[str, Any] | None:
    with transaction() as (_, cursor):
        cursor.execute(
            "SELECT id, username, role FROM web_users WHERE id = %s AND active = TRUE",
            (user_id,),
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return {"id": int(row["id"]), "username": row["username"], "role": row["role"]}


async def current_user(request: Request) -> dict[str, Any]:
    # Rol va faollik har so'rovda bazadan olinadi: o'chirilgan yoki roli o'zgargan foydalanuvchi darhol ta'sir qiladi.
    session = read_session(request.cookies.get(COOKIE_NAME))
    if session is None:
        raise HTTPException(status_code=401, detail="Tizimga kiring.")
    user = await run_in_threadpool(_load_active_user, session["id"])
    if user is None:
        raise HTTPException(status_code=401, detail="Tizimga kiring.")
    return user


def require_roles(*roles: str) -> Callable[..., Any]:
    async def check_role(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Bu amal uchun ruxsatingiz yo'q.")
        return user

    return check_role
