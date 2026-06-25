import cv2
import face_recognition
import numpy as np
from utils import (
    ensure_directories, get_face_encoding, save_encodings, 
    load_encodings, save_face_image, open_camera, read_input
)


def register_person():
    """Yangi odam qo'shish va yuzini ro'yxatga olish."""
    print("\n" + "="*50)
    print("YANGI ODAM ROʻYXATGA OLISH")
    print("="*50)
    
    name = read_input("Ismingizni kiriting: ")

    if name is None:
        return False
    
    if not name:
        print("❌ Ism bo'sh bo'lishi mumkin emas!")
        return False
    
    print(f"\n📹 Vebkamera ochilyapti... (2 soniya kutib turing)")
    print("Yuzingiz rasmga tushguncha kutib turing...")
    
    cap, camera_index = open_camera(width=640, height=480)
    
    if cap is None:
        print("❌ Vebkamera ulanmadi!")
        print("Kamera ulanganini va boshqa dastur ishlatmayotganini tekshiring.")
        return False

    print(f"📷 Kamera topildi: index {camera_index}")
    
    captured = False
    frame_count = 0
    target_frames = 15
    
    while not captured and frame_count < 150:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        frame = cv2.resize(frame, (640, 480))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if face_locations:
            frame_count += 1
            top, right, bottom, left = face_locations[0]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            progress = int((frame_count / target_frames) * 100)
            cv2.putText(frame, f"Yuz topildi! {progress}%", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if frame_count >= target_frames:
                encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                encodings = load_encodings()
                encodings[name] = encoding
                save_encodings(encodings)
                save_face_image(name, frame)
                captured = True
                print(f"\n✅ {name} muvaffaqiyatli roʻyxatga olinidi!")
        else:
            cv2.putText(frame, "Yuz topilmadi!", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Ro'yxatga olish", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n❌ Bekor qilindi!")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if not captured:
        print("\n❌ Yuz topilmadi yoki vaqt tugadi!")

    return captured


if __name__ == "__main__":
    ensure_directories()
    if register_person():
        response = read_input("\nYangi odam roʻyxatga olishni davom ettirmoqchimisiz? (ha/yo'q): ")
        response = response.lower() if response else ""
        if response in ['ha', 'yes', 'h', 'y']:
            register_person()
