import cv2  # type: ignore
import face_recognition  # type: ignore
import numpy as np  # type: ignore
import pickle
import dlib  # type: ignore
import logging
import os
import time
import threading
import hashlib
from pathlib import Path
import configparser

DATA_FILE = "registered_faces.pkl"
REGISTERED_DIR = "registered_faces"
CAMERA_INDEXES = (0, 1, 2, 3)

# --- Konfiguratsiyani o'qish ---
config = configparser.ConfigParser()
config.read('config.ini')

def get_config(section, key, fallback=None, type='str'):
    """Konfiguratsiyadan qiymatni xavfsiz olish."""
    value = config.get(section, key, fallback=fallback)
    if type == 'int':
        return int(value)
    if type == 'float':
        return float(value)
    if type == 'bool':
        return config.getboolean(section, key, fallback=fallback)
    return value

# GPU mavjudligini tekshirish
USE_GPU = dlib.DLIB_USE_CUDA if 'DLIB_USE_CUDA' in dlib.__dict__ else False
DETECTION_MODEL = get_config('performance', 'detection_model', fallback='hog') if USE_GPU else 'hog'

#sudo apt install nvidia-cuda-toolkit

def ensure_directories():
    """Papkalar mavjud bo'lishini tekshirish."""
    if not os.path.exists(REGISTERED_DIR):
        os.makedirs(REGISTERED_DIR)


def save_encodings(encodings_dict):
    """Yuzlarning kodlarini saqlash."""
    with open(DATA_FILE, 'wb') as f:
        pickle.dump(encodings_dict, f)


def load_encodings():
    """Saqlangan yuzlarning kodlarini yuklash."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'rb') as f:
            return pickle.load(f)
    return {}


def open_camera(width=None, height=None, camera_indexes=CAMERA_INDEXES):
    """Mavjud vebkamerani topib ochish."""
    if hasattr(cv2, "setLogLevel"):
        cv2.setLogLevel(0)

    available_indexes = [
        index for index in camera_indexes
        if os.path.exists(f"/dev/video{index}")
    ]
    indexes_to_try = available_indexes if os.name == "posix" else camera_indexes

    if os.name == "posix" and not indexes_to_try:
        return None, None

    # Linux tizimlarida avval V4L2, keyin standart usulni sinab ko'ramiz
    api_preferences = [cv2.CAP_V4L2, cv2.CAP_ANY] if os.name == "posix" else [cv2.CAP_ANY]

    for index in indexes_to_try:
        for api_preference in api_preferences:
            logging.info(f"Kamerani ochishga urinish: index={index}, API={api_preference}")
            cap = cv2.VideoCapture(index, api_preference)
            
            # Ba'zi drayverlar uchun kichik pauza kerak bo'lishi mumkin
            time.sleep(1) 

            if cap is None or not cap.isOpened():
                logging.warning(f"Kamerani ochib bo'lmadi (index={index}, API={api_preference}).")
                if cap: cap.release()
                continue

            # Kameradan kadr o'qish mumkinligini tekshirish
            ret, frame = cap.read()
            if ret and frame is not None:
                logging.info(f"✅ Kamera muvaffaqiyatli topildi va ishga tushirildi (index={index}, API={api_preference}).")
                if width: cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                if height: cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                return cap, index
            
            logging.warning(f"Kameradan kadr olinmadi (index={index}, API={api_preference}).")
            cap.release()

    return None, None


def read_input(prompt):
    """Interaktiv input mavjud bo'lmasa, None qaytaradi."""
    try:
        return input(prompt).strip() # logging.info o'rniga input ishlatiladi
    except EOFError:
        logging.error("Ma'lumot kiritilmadi. Skriptni terminalda interaktiv ishga tushiring.")
        return None


def get_face_encoding(image, face_location=None, num_jitters=1):
    """Rasmdan yuzning kodini olish."""
    known_face_locations = [face_location] if face_location else None
    face_encodings = face_recognition.face_encodings(
        image,
        known_face_locations=known_face_locations,
        num_jitters=num_jitters
    )
    if face_encodings:
        return face_encodings[0]
    return None


def speak(text):
    """Matnni ovozli ko'rinishda aytish (Alohida oqimda)."""
    def _speak():
        cache_dir = "voice_cache"
        assets_dir = "assets"
        os.makedirs(cache_dir, exist_ok=True)

        # Studiya fayllari (prefixlar bilan bog'langan)
        studio_files = {
            "Xush kelibsiz, ": os.path.join(assets_dir, "welcome_studio.mp3"),
            "Xayr, ": os.path.join(assets_dir, "goodbye_studio.mp3")
        }

        try:
            from gtts import gTTS  # type: ignore
            from pygame import mixer  # type: ignore
            
            mixer.init()
            prefix_file = None
            name_to_speak = text

            # Matndan prefixni qidirib topamiz va studiya faylini tekshiramiz
            for prefix, s_file in studio_files.items():
                if text.startswith(prefix) and os.path.exists(s_file):
                    prefix_file = s_file
                    name_to_speak = text.replace(prefix, "").strip()
                    break

            # Ismni gTTS orqali keshlaymiz
            name_hash = hashlib.md5(name_to_speak.encode()).hexdigest()
            name_path = os.path.join(cache_dir, f"{name_hash}.mp3")
            
            if not os.path.exists(name_path):
                gTTS(text=name_to_speak, lang='uz').save(name_path)

            if prefix_file:
                # 1. Professional audio (masalan, diktor aytgan "Xush kelibsiz")
                mixer.music.load(prefix_file)
                mixer.music.play()
                # 2. Xodim ismi (gTTS orqali generatsiya qilingan) navbatga qo'yiladi
                mixer.music.queue(name_path)
            else:
                # Studiya fayli bo'lmasa, to'liq matnni gTTS da aytish (fallback)
                mixer.music.load(name_path)
                mixer.music.play()

            while mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            logging.error(f"Ovozli xabarda xato: {e}")

    threading.Thread(target=_speak, daemon=True).start()


def record_audio(filename, duration=5):
    """
    Mikrofon orqali ovozni yozib oladi va .wav fayliga saqlaydi.
    """
    try:
        import pyaudio  # type: ignore
        import wave  # type: ignore

        chunk = 1024
        format = pyaudio.paInt16
        channels = 1
        rate = 44100

        p = pyaudio.PyAudio()
        stream = p.open(format=format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)

        logging.info(f"🎤 Ovoz yozish boshlandi: {duration} soniya...")
        frames = []

        for i in range(0, int(rate / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)

        logging.info("✅ Ovoz yozish tugadi.")

        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
        return True
    except Exception as e:
        logging.error(f"Ovoz yozishda xato: {e}")
        return False


def face_distance_to_confidence(face_distance, tolerance=0.6):
    """Face distance qiymatini 0-100 oralig'idagi aniqlik foiziga aylantirish."""
    if face_distance <= 0:
        return 100.0
    if face_distance > tolerance:
        # Mos kelmasa foizni juda past ko'rsatish
        return max(0.0, (1.0 - face_distance) * 40.0)

    # CNN modeli bilan masofa odatda kichikroq bo'ladi
    # 0.6 -> 85%, 0.4 -> 95%, 0.2 -> 99%
    confidence = (1.0 - (face_distance / (tolerance * 1.5))**2) * 100
    return max(0.0, min(100.0, confidence))


def encode_face_photo(frame, top, right, bottom, left, padding=60):
    """Yuz atrofidan rasm kesib, Telegram uchun JPEG bytes qaytaradi."""
    height, width = frame.shape[:2]
    top = max(0, top - padding)
    left = max(0, left - padding)
    bottom = min(height, bottom + padding)
    right = min(width, right + padding)

    if bottom <= top or right <= left:
        return None

    face_image = frame[top:bottom, left:right]
    ok, buffer = cv2.imencode(".jpg", face_image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        return None
    return buffer.tobytes()


def detect_faces(image):
    """Rasmda yuzlarni aniqlash."""
    face_locations = face_recognition.face_locations(image, model=DETECTION_MODEL)
    return face_locations


def compare_faces(known_encodings_dict, test_encoding, tolerance=0.6):
    """Yuzni taqqoslash va ismini topish."""
    if not known_encodings_dict:
        return None, 0.0
    
    # Lug'atni har safar listga aylantirmaslik uchun keshlasa bo'ladi, 
    # lekin hozirgi holatda ham barqaror ishlaydi.
    names = list(known_encodings_dict.keys())
    encodings = list(known_encodings_dict.values())
    
    distances = face_recognition.face_distance(encodings, test_encoding)
    
    if len(distances) == 0:
        return None, 0.0
    
    min_distance_index = np.argmin(distances)
    min_distance = distances[min_distance_index]
    
    if min_distance < tolerance:
        return names[min_distance_index], min_distance
    
    return None, min_distance


def save_face_image(name, image):
    """Surat faylini saqlash."""
    ensure_directories()
    path = os.path.join(REGISTERED_DIR, f"{name}.jpg")
    cv2.imwrite(path, image)


def get_all_registered_names():
    """Roʻyxatga olingan barcha odamlarning ismlarini olish."""
    encodings = load_encodings()
    return list(encodings.keys())


def draw_label(frame, name, confidence, top, right, bottom, left, status=None):
    """Yuzning ustiga ismini va ishonch darajasini yozish."""
    label = f"{name}: {confidence:.1f}%" if name != "Noma'lum" else "Noma'lum"
    color = (0, 255, 0) if name != "Noma'lum" else (0, 0, 255)
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.rectangle(frame, (left, top - 35), (right, top), color, cv2.FILLED)
    cv2.putText(frame, label, (left + 6, top - 6),
               cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

    # Status ko'rsatish (Kelib / Ketgan)
    if status:
        status_text = "KELIB ✓" if status == "entry" else "KETGAN ✗"
        cv2.putText(frame, status_text, (left + 6, bottom + 20),
                   cv2.FONT_HERSHEY_DUPLEX, 0.5, color, 1)
