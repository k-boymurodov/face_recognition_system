# 🏦 BANK DAVOMAT TIZIMI - O'RNATISH QILAVARI

## ⚡ TEZKOR O'RNATISH (5 DAQIQA)

### Qadam 1: Kutubxonalarni o'rnatish
```bash
cd /home/kamronbek/Desktop/face_recognition_system
pip install --break-system-packages -r requirements.txt
```

### Qadam 2: Bazani o'rnatish
```bash
python3 setup_database.py
```

### Qadam 3: Tezkor ishga tushirish
```bash
python3 quickstart.py
```

---

## ✅ TEKSHIRISH

### 1. Python kutubxonalari:
```bash
python3 -c "import cv2, face_recognition, numpy; print('OK')"
```

### 2. Baza tekshirish:
```bash
python3 -c "from database import get_connection; print('Connected!' if get_connection() else 'Error')"
```

---

## 🚀 ISHLATISH

```bash
# 1. Xodim qo'shish
python3 register_employee.py

# 2. Davomat tizimi
python3 attendance_system.py

# 3. Hisobotlar
python3 reports.py
```

---

## ❓ TEZKOR YECHIMLAR

| Muammo | Yechim |
|--------|--------|
| Baza topilmadi | `python3 setup_database.py` |
| Kutubxona xatosi | `pip install --break-system-packages -r requirements.txt` |
| Vebkamera xatosi | `sudo chmod 666 /dev/video*` |

**TAYYOR! 🎉**
