from dataclasses import dataclass
from io import BytesIO

import cv2
import face_recognition
import numpy as np
from PIL import Image

from backend.config import settings
from backend.database import transaction

# Eng yaqin va ikkinchi eng yaqin xodim orasidagi minimal masofa farqi (o'xshash yuzlarni adashtirmaslik uchun).
MATCH_MARGIN = 0.05


@dataclass
class FaceResult:
    boxes: list[dict[str, float]]
    encoding: np.ndarray | None = None


def decode_image(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise ValueError("Rasm bo'sh yuborildi.")
    if len(image_bytes) > 5 * 1024 * 1024:
        raise ValueError("Rasm hajmi 5 MB dan oshmasligi kerak.")
    # O'lcham rasmni to'liq ochishdan OLDIN tekshiriladi (kichik fayl, lekin ulkan piksel sonli rasmdan himoya).
    try:
        with Image.open(BytesIO(image_bytes)) as probe:
            fmt, (width, height) = probe.format, probe.size
    except Exception:
        raise ValueError("Rasm formati JPEG yoki PNG bo'lishi kerak.")
    if fmt not in {"JPEG", "PNG"}:
        raise ValueError("Rasm formati JPEG yoki PNG bo'lishi kerak.")
    if width < 160 or height < 120 or width > 4096 or height > 4096:
        raise ValueError("Rasm o'lchami qo'llab-quvvatlanmaydi.")
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Rasm formati JPEG yoki PNG bo'lishi kerak.")
    return image


def analyze_image(image_bytes: bytes, require_single: bool = False) -> FaceResult:
    image = decode_image(image_bytes)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model="hog")
    boxes = [
        {
            "top": top / image.shape[0],
            "right": right / image.shape[1],
            "bottom": bottom / image.shape[0],
            "left": left / image.shape[1],
        }
        for top, right, bottom, left in locations
    ]
    if not require_single:
        return FaceResult(boxes=boxes)
    if not locations:
        raise ValueError("Yuz topilmadi. Yorug' joyda kameraga qarang.")
    if len(locations) != 1:
        raise ValueError("Kadrda aynan bitta yuz bo'lishi kerak.")

    top, right, bottom, left = locations[0]
    if right - left < 80 or bottom - top < 80:
        raise ValueError("Yuz kameraga yaqinroq bo'lishi kerak.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if cv2.Laplacian(gray, cv2.CV_64F).var() < 12:
        raise ValueError("Tasvir xira. Kamerani barqaror tutib qayta oling.")
    encodings = face_recognition.face_encodings(rgb, locations, num_jitters=1)
    if not encodings:
        raise ValueError("Yuz sifati yetarli emas. Qayta urinib ko'ring.")
    return FaceResult(boxes=boxes, encoding=encodings[0])


def known_face_encodings(
    exclude_employee_id: int | None = None,
    include_inactive: bool = False,
) -> list[tuple[int, str, np.ndarray]]:
    with transaction() as (_, cursor):
        query = "SELECT id, name, face_encoding FROM employees"
        if not include_inactive:
            query += " WHERE status = 'active'"
        cursor.execute(query)
        employees = cursor.fetchall()

    known = []
    for employee in employees:
        if exclude_employee_id is not None and int(employee["id"]) == exclude_employee_id:
            continue
        blob = bytes(employee["face_encoding"] or b"")
        if len(blob) != 128 * np.dtype(np.float64).itemsize:
            continue
        encoding = np.frombuffer(blob, dtype=np.float64)
        if np.isfinite(encoding).all():
            known.append((int(employee["id"]), employee["name"], encoding))
    return known


def find_duplicate(encoding: np.ndarray, exclude_employee_id: int | None = None):
    known = known_face_encodings(exclude_employee_id, include_inactive=True)
    if not known:
        return None
    distances = face_recognition.face_distance([item[2] for item in known], encoding)
    best_index = int(np.argmin(distances))
    distance = float(distances[best_index])
    if distance <= settings.face_tolerance:
        employee_id, name, _ = known[best_index]
        return {"employee_id": employee_id, "name": name, "distance": distance}
    return None


def match_employee(encoding: np.ndarray):
    known = known_face_encodings()
    if not known:
        return None
    distances = face_recognition.face_distance([item[2] for item in known], encoding)
    best_index = int(np.argmin(distances))
    distance = float(distances[best_index])
    if distance > settings.face_tolerance:
        return None
    # Ikkinchi eng yaqin xodim deyarli bir xil masofada bo'lsa, adashmaslik uchun tanimaymiz.
    if len(distances) > 1 and float(np.partition(distances, 1)[1]) - distance < MATCH_MARGIN:
        return None
    employee_id, name, _ = known[best_index]
    return {
        "id": employee_id,
        "name": name,
        "distance": distance,
        "confidence": round(max(0.0, 100.0 * (1.0 - distance / settings.face_tolerance)), 1),
    }
