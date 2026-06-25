import cv2  # type: ignore
import face_recognition  # type: ignore
import numpy as np  # type: ignore
from utils import (
    ensure_directories, get_face_encoding, save_encodings, get_config,
    load_encodings, save_face_image, open_camera, read_input, DETECTION_MODEL
)
from database import add_employee
import logging


def register_employee_with_db():
    """Yangi xodim qo'shish va bazada saqlash."""
    logging.info("="*50)
    logging.info("YANGI XODIM ROʻYXATGA OLISH")
    logging.info("="*50)
    
    name = read_input("Xodimning to'liq ismini kiriting: ")
    if name is None:
        return False
    if not name:
        logging.error("Ism bo'sh bo'lishi mumkin emas!")
        return False
    
    department = read_input("Departament (ixtiyoriy): ")
    if department is None:
        return False
    department = department or "Noma'lum"

    position = read_input("Lavozim (ixtiyoriy): ")
    if position is None:
        return False
    position = position or "Noma'lum"
    
    logging.info("📹 Vebkamera ochilyapti...")
    logging.info("Yuzingiz rasmga tushguncha kutib turing...")
    
    # Konfiguratsiyadan kamera o'lchamlarini olish
    cam_width = get_config('camera', 'width', fallback=640, type='int')
    cam_height = get_config('camera', 'height', fallback=480, type='int')
    cap, camera_index = open_camera(width=cam_width, height=cam_height)
    
    if cap is None:
        logging.error("Vebkamera ulanmadi! Kamera ulanganini va boshqa dastur ishlatmayotganini tekshiring.")
        return False

    logging.info(f"Kamera topildi: index {camera_index}")

    # Konfiguratsiyadan ro'yxatga olish parametrlarini olish
    target_frames = get_config('recognition', 'registration_frames', fallback=15, type='int')
    num_jitters = get_config('recognition', 'registration_jitters', fallback=10, type='int')
    captured = False
    frame_count = 0
    encodings_list = []
    
    while not captured and frame_count < 150:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Yoritishni optimallashtirish (CLAHE)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        frame = cv2.merge((cl,a,b))
        frame = cv2.cvtColor(frame, cv2.COLOR_LAB2BGR)
        frame = cv2.resize(frame, (cam_width, cam_height))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame, model=DETECTION_MODEL)
        
        if face_locations:
            frame_count += 1
            top, right, bottom, left = face_locations[0]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            progress = int((frame_count / target_frames) * 100)
            cv2.putText(frame, f"Yuz topildi! {progress}%", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if frame_count >= target_frames:
                # Ro'yxatga olishda yuqori aniqlik uchun num_jitters=10
                current_enc = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=num_jitters)[0]
                encodings_list.append(current_enc)
                captured = True
                logging.info(f"{name} yuzlari qayd qilindi!")
            else:
                # Har bir kadr uchun kodni yig'ish
                current_enc = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                encodings_list.append(current_enc)
        else:
            cv2.putText(frame, "Yuz topilmadi!", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Xodim Ro'yxatga Olish", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            logging.warning("Bekor qilindi!")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if not captured or not encodings_list:
        logging.error("Yuz topilmadi yoki vaqt tugadi!")
        return False
    
    # Barcha olingan kodlarning o'rtachasini hisoblash (Accuracy boost)
    face_encoding = np.mean(encodings_list, axis=0)
    
    # Pickle format'da saqlash
    try: # Ma'lumotlar bazasiga yozish
        employee_id = add_employee(name, face_encoding, department, position)
        
        if employee_id:
            logging.info(f"{name} muvaffaqiyatli ro'yxatga olinidi!")
            logging.info(f"Xodim ID: {employee_id}")
            logging.info(f"Departament: {department}")
            logging.info(f"Lavozim: {position}")
            return True
        else:
            logging.error("Xodim qo'shishda xato!")
            return False
            
    except Exception as e:
        logging.error(f"Xato: {e}")
        return False


if __name__ == "__main__":
    from logging_config import setup_logging
    setup_logging()
    
    ensure_directories()
    while True:
        if not register_employee_with_db():
            break
        response = read_input("\nYangi xodim roʻyxatga olishni davom ettirasizmi? (ha/yo'q): ")
        if not response or response.lower() not in ['ha', 'yes', 'h', 'y']:
            break
