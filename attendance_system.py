import cv2  # type: ignore
import face_recognition  # type: ignore
import dlib  # type: ignore
import numpy as np  # type: ignore
import pickle
import time 
import threading
from utils import open_camera, encode_face_photo, face_distance_to_confidence, speak, DETECTION_MODEL, compare_faces, get_config
from utils import draw_label as draw_face_label # draw_label funksiyasini utils.py dan import qilish
from datetime import datetime, timedelta
from database import ( # noqa
    get_all_employees, record_attendance, get_daily_attendance,
    get_attendance_report, get_attendance_log, get_employee_by_name, log_unknown_person,
    get_next_attendance_action
)
import logging
from telegram_bot import send_attendance_notification, is_telegram_configured, send_unknown_person_alert

class VideoStream:
    """Kamerani alohida oqimda o'qish (Qotishni oldini olish uchun)."""
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.cap, self.index = open_camera(width=self.width, height=self.height)
        self.ret, self.frame = (False, None)
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if self.cap is not None:
                self.ret, self.frame = self.cap.read()
            if not self.ret:
                time.sleep(0.1)
                if self.cap is not None: self.cap.release()
                self.cap, _ = open_camera(width=self.width, height=self.height)
                continue

    def stop(self):
        self.stopped = True
        if self.cap: self.cap.release()


def get_employee_encodings():
    """Barcha xodimlarning yuz kodlarini olish."""
    employees = get_all_employees()
    
    if not employees: # logging.warning
        logging.warning("Hech qanday xodim ro'yxatga olinmadi!")
        return {}, {}
    
    known_encodings = {}
    employee_ids = {}
    
    # Tezlik uchun ro'yxatlarni oldindan tayyorlaymiz
    for emp in employees:
        try:
            # Ma'lumotlar bazasidan to'g'ridan-to'g'ri baytlarni o'qish
            encoding = np.frombuffer(emp['face_encoding'], dtype=np.float64)
            known_encodings[emp['name']] = encoding
            employee_ids[emp['name']] = emp['id']
        except Exception as e:
            logging.warning(f"{emp['name']} kodini yuklashda xato: {e}")
    
    return known_encodings, employee_ids


def process_background_tasks(name, employee_id, status, confidence, frame, loc):
    """Og'ir vazifalarni fonda bajarish (DB, Telegram, Voice)."""
    photo_bytes = encode_face_photo(frame, loc[0], loc[1], loc[2], loc[3])
    if record_attendance(employee_id, status, confidence):
        send_attendance_notification(name, status, confidence, photo_bytes)
        logging.info(f"✅ {name} uchun {status} qayd etildi.")
        greeting = f"Xush kelibsiz, {name}" if status == 'entry' else f"Xayr, {name}"
        speak(greeting)

def process_unknown_person_task(frame, loc):
    """Noma'lum shaxsni fonda qayta ishlash (DB, Telegram)."""
    photo_bytes = encode_face_photo(frame, loc[0], loc[1], loc[2], loc[3])
    if photo_bytes:
        log_unknown_person(photo_bytes)
        send_unknown_person_alert(photo_bytes)

def process_frame_for_recognition(frame, frame_count, known_faces_list, known_names, employee_ids, last_recognition, last_unknown_alert_time):
    """
    Bitta kadrni olib, yuzni tanishni amalga oshiradi va natijalarni qaytaradi.
    Bu funksiya app.py tomonidan chaqiriladi.
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    current_time = datetime.now()
    face_locations = []
    face_names_data = []

    # Konfiguratsiyadan qiymatlarni olish
    process_every_n_frame = get_config('performance', 'process_every_n_frame', fallback=2, type='int')
    frame_resize_factor = get_config('performance', 'frame_resize_factor', fallback=0.25, type='float')
    tolerance = get_config('recognition', 'tolerance', fallback=0.5, type='float')
    recognition_cooldown = get_config('alerts', 'recognition_cooldown', fallback=10, type='int')
    unknown_person_cooldown = get_config('alerts', 'unknown_person_alert_cooldown', fallback=30, type='int')

    if frame_count % process_every_n_frame == 0:
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=frame_resize_factor, fy=frame_resize_factor)
        raw_face_locations = face_recognition.face_locations(small_frame, model=DETECTION_MODEL)
        face_encodings = face_recognition.face_encodings(small_frame, raw_face_locations)

        scale = 1 / frame_resize_factor
        face_locations = [(int(top*scale), int(right*scale), int(bottom*scale), int(left*scale)) for top, right, bottom, left in raw_face_locations]
        
        for i, face_encoding in enumerate(face_encodings):
            distances = face_recognition.face_distance(known_faces_list, face_encoding)
            best_match_index = np.argmin(distances)
            distance = distances[best_match_index]
            
            name = "Noma'lum"
            if distance < tolerance:
                name = known_names[best_match_index]

            confidence = face_distance_to_confidence(distance, tolerance=tolerance)
            
            if name != "Noma'lum":
                employee_id = employee_ids[name]
                current_expected_status = get_next_attendance_action(employee_id)
                last_time = last_recognition.get(name)
                if last_time is None or (current_time - last_time).seconds > recognition_cooldown:
                    loc = face_locations[i]
                    threading.Thread(target=process_background_tasks, args=(name, employee_id, current_expected_status, confidence, frame, loc), daemon=True).start()
                    last_recognition[name] = current_time
                face_names_data.append((name, confidence, current_expected_status))
            else:
                face_names_data.append(("Noma'lum", confidence, None))
                if last_unknown_alert_time is None or (current_time - last_unknown_alert_time).seconds > unknown_person_cooldown:
                    logging.warning("Noma'lum shaxs aniqlandi! Ogohlantirish yuborilmoqda...")
                    loc = face_locations[i]
                    threading.Thread(target=process_unknown_person_task, args=(frame, loc), daemon=True).start()
                    last_unknown_alert_time = current_time

    # Natijalarni kadrga chizish
    draw_recognition_results(frame, face_locations, face_names_data)
    return frame, last_recognition, last_unknown_alert_time

def draw_recognition_results(frame, face_locations, face_names_data):
    """Tanish natijalarini kadrga chizadi."""
    for i, (top, right, bottom, left) in enumerate(face_locations):
        if i < len(face_names_data):
            n, c, s = face_names_data[i]
            draw_face_label(frame, n, c, top, right, bottom, left, s)

def main():
    """Davomat tizimi: xodimlarni taniş va bazada saqlash."""
    from logging_config import setup_logging
    setup_logging()

    logging.info("="*60)
    logging.info("🏦 BANK XODIM DAVOMAT TIZIMI")
    logging.info("="*60)
    logging.info("Xodimlarning kelib ketishini qayd qilish")
    logging.info("Chiqish uchun 'q' tugmasini bosing\n")
    
    known_encodings, employee_ids = get_employee_encodings()
    # Ma'lumotlarni tezroq qidirish uchun ro'yxat ko'rinishiga o'tkazamiz
    known_names = list(known_encodings.keys())
    known_faces_list = list(known_encodings.values())
    
    if not known_encodings:
        logging.error("Xodimlarni qaydlash zarur! Avval 'register_employee.py' bilan xodim qo'shing.")
        return
    
    logging.info(f"{len(known_encodings)} ta xodim o'rnatildi")
    if is_telegram_configured():
        logging.info("Telegram xabarlari yoqilgan")
    else:
        logging.warning("Telegram sozlanmagan. .env fayliga TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID yozing.")
    
    if DETECTION_MODEL == "cnn":
        logging.info("🚀 GPU (NVIDIA CUDA) tezlatgichi ishga tushirildi!")
    else:
        logging.info("💻 CPU rejimida ishlamoqda (GPU topilmadi).")
    
    vs = VideoStream().start()
    time.sleep(2.0) # Kamera isishi uchun
    
    last_recognition = {}
    last_unknown_alert_time = None
    frame_count = 0

    face_locations = []
    face_names_data = []
    
    while True:
        if not vs.ret or vs.frame is None:
            logging.warning("Kamera uzildi. Qayta ulanishga harakat qilinmoqda...")
            time.sleep(1)
            continue

        frame = vs.frame.copy()
        
        # Kadrni qayta ishlash
        processed_frame, last_recognition, last_unknown_alert_time = process_frame_for_recognition(
            frame, frame_count, known_faces_list, known_names, employee_ids, last_recognition, last_unknown_alert_time
        )

        # Keshdagi ma'lumotlarni chizish
        draw_recognition_results(processed_frame, face_locations, face_names_data)
        
        # Ekranda ma'lumotlar
        today = datetime.now().strftime("%d.%m.%Y")
        cv2.putText(processed_frame, f"Sana: {today}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(processed_frame, f"Vaqt: {datetime.now().strftime('%H:%M:%S')}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(processed_frame, f"Taniş: {len(last_recognition)} ta", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("Davomat Tizimi", processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            logging.info("Tizim to'xtatildi.")
            vs.stop()
            cv2.destroyAllWindows()
            return

        frame_count += 1


def main_cli():
    """Davomat tizimini konsol orqali ishga tushirish uchun eski funksiya."""
    from logging_config import setup_logging
    setup_logging()

    logging.info("="*60)
    logging.info("🏦 BANK XODIM DAVOMAT TIZIMI (CLI)")
    logging.info("="*60)
    
    known_encodings, employee_ids = get_employee_encodings()
    known_names = list(known_encodings.keys())
    known_faces_list = list(known_encodings.values())
    
    if not known_encodings:
        logging.error("Xodimlarni qaydlash zarur! Avval 'register_employee.py' bilan xodim qo'shing.")
        return

    vs = VideoStream().start()
    time.sleep(2.0)
    
    last_recognition = {}
    last_unknown_alert_time = None
    frame_count = 0

    while True:
        try:
            if not vs.ret or vs.frame is None:
                time.sleep(1)
                continue

            frame = vs.frame.copy()
            
            frame_count += 1

            # Ekranda ma'lumotlar
            today = datetime.now().strftime("%d.%m.%Y")
            cv2.putText(frame, f"Sana: {today}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Vaqt: {datetime.now().strftime('%H:%M:%S')}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Taniş: {len(last_recognition)} ta", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Davomat Tizimi (CLI)", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("Tizim to'xtatildi.")
                vs.stop()
                cv2.destroyAllWindows()
                return
            
        except Exception as e:
            logging.error(f"Kutilmagan xato: {e}. 10 soniyadan so'ng davom etadi.")
            time.sleep(10)
            continue
    
    # Kunlik hisobi
    logging.info("="*60)
    logging.info("📊 KUNLIK DAVOMAT HISOBI")
    logging.info("="*60)
    
    daily_attendance = get_daily_attendance()
    for record in daily_attendance:
        entry = record['entry_time'].strftime('%H:%M') if record['entry_time'] else "-"
        exit_time = record['exit_time'].strftime('%H:%M') if record['exit_time'] else "-"
        logging.info(f"👤 {record['name']:20} | {entry:6} → {exit_time:6} | {record['department']}")


if __name__ == "__main__":
    main_cli()
