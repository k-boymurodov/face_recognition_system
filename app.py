from flask import Flask, render_template, jsonify, Response
from datetime import datetime
import logging
from logging_config import setup_logging
import os
import cv2
import threading
import time

# Yuzni tanish tizimidan kerakli funksiyalarni import qilamiz
from attendance_system import (
    get_employee_encodings,
    process_frame_for_recognition,
    draw_recognition_results
)
from utils import open_camera, get_config
from database import get_daily_attendance

# Logging sozlamalarini ishga tushirish
setup_logging()

# Shablonlar jildiga to'liq yo'lni ko'rsatish (barqarorlik uchun)
# Bu qator `app.py` fayli joylashgan papkani topadi
project_root_path = os.path.dirname(os.path.abspath(__file__))
# `templates` jildining to'liq manzilini yaratadi
app = Flask(__name__, template_folder=project_root_path)

# Flask'ning o'zining loggerini o'chiramiz, bizning umumiy loggerimizni ishlatish uchun
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

# --- Real-time monitoring uchun global o'zgaruvchilar ---
output_frame = None
lock = threading.Lock()
camera_thread = None

def recognition_thread():
    """
    Kameradan kadr olib, yuzni tanishni alohida oqimda bajaradigan funksiya.
    """
    global output_frame, lock

    # Xuddi attendance_system.py dagi kabi sozlash
    known_encodings, employee_ids = get_employee_encodings()
    known_names = list(known_encodings.keys())
    known_faces_list = list(known_encodings.values())

    if not known_encodings:
        logging.error("Xodimlarni qaydlash zarur! Avval 'register_employee.py' bilan xodim qo'shing.")
        return

    cam_width = get_config('camera', 'width', fallback=640, type='int')
    cam_height = get_config('camera', 'height', fallback=480, type='int')
    cap, _ = open_camera(width=cam_width, height=cam_height)

    if cap is None:
        logging.error("Kamera topilmadi!")
        return

    last_recognition = {}
    last_unknown_alert_time = None
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.warning("Kameradan kadr olinmadi. Qayta ulanishga harakat qilinmoqda...")
            time.sleep(2)
            cap.release()
            cap, _ = open_camera(width=cam_width, height=cam_height)
            continue

        # Yuzni tanish va chizish
        processed_frame, last_recognition, last_unknown_alert_time = process_frame_for_recognition(
            frame, frame_count, known_faces_list, known_names, employee_ids, last_recognition, last_unknown_alert_time
        )

        frame_count += 1

        # Oqim uchun kadrni yangilash
        with lock:
            output_frame = processed_frame.copy()

def generate_video_stream():
    """
    Video kadrlarni MJPEG formatida uzluksiz yuborib turadi.
    """
    global output_frame, lock

    while True:
        with lock:
            if output_frame is None:
                continue
            # Kadrlarni JPEG formatiga o'tkazish
            (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue

        # Kadrlarni 'yield' orqali qaytarish
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route('/')
def dashboard():
    """
    Asosiy boshqaruv paneli (Dashboard).
    Kunlik davomatni ko'rsatadi.
    """
    try:
        return render_template('index.html', today=datetime.now().strftime('%d.%m.%Y'))
    except Exception as e:
        logging.error(f"Dashboard sahifasini yuklashda xato: {e}")
        return render_template('error.html', error_message=str(e))

@app.route('/video_feed')
def video_feed():
    """Video oqimini qaytaradigan manzil."""
    return Response(generate_video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route('/api/daily_attendance')
def api_daily_attendance():
    """Kunlik davomat ma'lumotlarini JSON formatida qaytaradi."""
    today = datetime.now().date()
    records = get_daily_attendance(today)
    return jsonify(records)


if __name__ == '__main__':
    # Yuzni tanish oqimini ishga tushirish
    camera_thread = threading.Thread(target=recognition_thread, daemon=True)
    camera_thread.start()

    logging.info("="*50)
    logging.info("🚀 Veb Boshqaruv Paneli ishga tushmoqda...")
    logging.info("🌐 Ochish uchun bosing: http://127.0.0.1:5000")
    logging.info("="*50)
    # debug=True - ishlab chiqish uchun qulay, lekin production'da False bo'lishi kerak
    app.run(host='0.0.0.0', port=5000, debug=True)