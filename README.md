# 👤 Yuz Tanish Tizimi (Face Recognition System)

Ushbu dastur vebkamera yordamida odamlarning yuzlarini tanishni va ularni roʻyxatga olishni taqdim etadi.

## 📦 O'rnatish

### 1️⃣ Kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

**Zarur kutubxonalar:**
- `opencv-python` - Video va rasm qayta ishlash
- `face-recognition` - Yuz tanish (dlib-based)
- `numpy` - Sonli hisob-kitoblar
- `Pillow` - Rasm qayta ishlash

### 2️⃣ Papkalar yaratish:
Dastur avtomatik ravishda `registered_faces/` papkasini yaratadi.

## 🚀 Foydalanish

### 📝 1. Yangi odam qo'shish:

```bash
python register.py
```

**Qadam-qadam:**
1. Ismingizni kiriting
2. Vebkameraga qarang
3. Dastur 2-3 soniya ichida yuzingizni 15-20 kadriga oladi
4. Avtomatik saqlash va "Ro'yxatga olindi" xabari

**✅ Muvaffaqiyatli bo'lsa:**
- Yuzning kodi `registered_faces.pkl` faylida saqlana
- Rasm `registered_faces/` papkasida saqlana

---

### 🎥 2. Asosiy dastur (Yuzlarni tanish):

```bash
python main.py
```

**Nima qiladi:**
- Vebkameraga qarang
- Taniş olamlarning yuzlari **yashil** to'rtburchak bilan ko'rsatiladi
- Noma'lum yuzlar **qizil** to'rtburchak bilan ko'rsatiladi
- Ishonch darajasi (confidence %) ko'rsatiladi
- **Chiqish:** `q` tugmasini bosing

---

## 📂 Fayl Tuzilishi

```
face_recognition_system/
├── main.py                  # Asosiy dastur (vebkamera + taniş)
├── register.py              # Yangi odam qo'shish
├── utils.py                 # Yordamchi funksiyalar
├── requirements.txt         # Kutubxonalar
├── README.md                # Bu fayl
├── registered_faces.pkl     # Saqlangan yuzlar (avtomatik)
└── registered_faces/        # Yuzlarning rasmlar (avtomatik)
```

---

## 🔧 Amaliy Misol

### Birinchi marta:

```bash
# 1. Dependencies o'rnatish
pip install -r requirements.txt

# 2. Odam qo'shish (masalan, Ali)
python register.py
# Ismingizni kiriting: Ali
# [Vebkameraga qarang 2 soniya]
# ✅ Ali muvaffaqiyatli roʻyxatga olinidi!

# 3. Yana bir odam qo'shish
# Ismingizni kiriting: Zarrina
# [Vebkameraga qarang 2 soniya]
# ✅ Zarrina muvaffaqiyatli roʻyxatga olinidi!

# 4. Asosiy dasturnni ishlatish
python main.py
# Ali va Zarrina yuzlari YASHIL rangli bo'ladi
# O'zga odamlar QIZIL rangli bo'ladi
```

---

## ⚙️ Taqqoslash Parametrlari (utils.py)

```python
tolerance = 0.6  # Yuzlarni taqqoslash darajasi
# Qo'pol (0.6 +):  Ko'p noto'g'ri tanishlar, lekin sezuvchan
# O'rtacha (0.5):  Balansli
# Aniq (0.4 -):    Kamroq xato, lekin ayrim odamlarni o'tkazib yuborishi mumkin
```

---

## 🐛 Muammolar va Yechimlar

### ❌ "Vebkamera ulanmadi"
- Vebkamera konektsiasini tekshiring
- Boshqa dasturlar vebkamerni ishlatayotganini tekshiring
- Terminal bilan: `ls /dev/video*`

### ❌ "Hali hech qanday yuz ro'yxatga olinmadi"
- Avval `register.py` bilan odam qo'shing
- Fayl bo'lsa: `ls registered_faces.pkl`

### ❌ Yuzni tanishan, lekin noto'g'ri ism
- Parametrni qisqart ting: `tolerance` ni 0.5 ga o'zgartiring
- Yozdan qayta qo'shing: `register.py` ishlatib

### ❌ "ModuleNotFoundError: No module named 'face_recognition'"
```bash
# Qayta o'rnatish
pip install --upgrade face-recognition
# Yoki dlib bilan
pip install dlib face-recognition
```

---

## 🎯 Xususiyatlar

✅ Real-time yuz taniş  
✅ Osongina yangi odamni qo'shish  
✅ Vebkameracha direktno ishlatish  
✅ Saqlangan ma'lumotlar xavfsiz  
✅ Ishonch darajasi ko'rsatish  

---

## 📚 Texnik Tafsif

**Yuz kodlash (Face Encoding):**
- `face_recognition` kutubxonasi 128-o'lchamli vektor yaratadi
- Har bir yuz noyob kodga ega
- Taqqoslash: `face_distance()` - hech qancha 0-1 oraligida

**Saqlash:**
- `pickle` - Python ob'ektlarini saqlash
- `registered_faces.pkl` - Barcha yuzlar

---

## 📞 Qo'shimcha

- **Muallif:** Tizim Rivojlantirish
- **Til:** Uzbek (O'zbek)
- **Versiya:** 1.0

Savollar bo'lsa, kodlarni tekshiring! 🚀
