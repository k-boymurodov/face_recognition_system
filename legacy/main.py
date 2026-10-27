import cv2
import face_recognition
import numpy as np
from datetime import datetime
from utils import (
    ensure_directories, load_encodings, detect_faces, 
    compare_faces, get_face_encoding, open_camera
)


def draw_label(frame, name, confidence, top, right, bottom, left):
    """Yuzning ustiga ismini va ishonch darajasini yozish."""
    label = f"{name}: {confidence:.1f}%" if name != "Noma'lum" else "Noma'lum"
    color = (0, 255, 0) if name != "Noma'lum" else (0, 0, 255)
    
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.rectangle(frame, (left, top - 35), (right, top), color, cv2.FILLED)
    cv2.putText(frame, label, (left + 6, top - 6),
               cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)


def main():
    """Asosiy dastur: vebkameracha yuzlarni aniqlash."""
    print("\n" + "="*50)
    print("YUZ TANIŞ TIZIMI")
    print("="*50)
    print("Chiqish uchun 'q' tugmasini bosing\n")
    
    ensure_directories()
    known_encodings = load_encodings()
    
    if not known_encodings:
        print("⚠️  Hali hech qanday yuz roʻyxatga olinmadi!")
        print("Iltimos, avval 'register.py' bilan odam qo'shib ko'ring.\n")
        return
    
    print(f"✅ {len(known_encodings)} ta odam roʻyxatga olingan\n")
    
    cap, camera_index = open_camera(width=640, height=480)
    
    if cap is None:
        print("❌ Vebkamera ulanmadi!")
        print("Kamera ulanganini va boshqa dastur ishlatmayotganini tekshiring.")
        return

    print(f"📷 Kamera topildi: index {camera_index}")
    
    recognized_people = {}
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Kadri o'qiyolmadi!")
            break
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = detect_faces(rgb_frame)
        
        for top, right, bottom, left in face_locations:
            face_encoding = get_face_encoding(rgb_frame, (top, right, bottom, left))
            
            if face_encoding is not None:
                name, distance = compare_faces(known_encodings, face_encoding)
                confidence = max(0, (1 - distance) * 100) if name else 0
                
                if not name:
                    name = "Noma'lum"
                    confidence = 0
                else:
                    if name not in recognized_people:
                        recognized_people[name] = datetime.now()
                
                draw_label(frame, name, confidence, top, right, bottom, left)
        
        info_text = f"Taniş: {len(recognized_people)} ta | Kadalar: {cap.get(cv2.CAP_PROP_POS_FRAMES):.0f}"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow("Yuz Taniş Tizimi", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n✅ Chiqilmoqda...\n")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if recognized_people:
        print("\n📊 TAN OLINGAN ODAMLAR:")
        for name, time in recognized_people.items():
            print(f"  • {name} - {time.strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
