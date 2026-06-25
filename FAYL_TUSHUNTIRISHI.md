# 📑 LOYIHA FAYLLARINING TUSHUNTIRISHI

## 🏦 Bank Xodim Davomat Tizimi

---

## 📄 ASOSIY FAYLLAR

### 1. `attendance_system.py` 🎥 (ASOSIY)
**Maqsadi:** Vebkameracha xodimlarning kelib ketishini taniş qilish

- ✅ Vebkameradan yuz taniydi
- ✅ Xodimni bazada topadi
- ✅ KELIB (entry) yoki KETGAN (exit) belgilaydi
- ✅ Bazaga avtomatik qayd qiladi
- ✅ Kunlik hisobi ko'rsatadi

**Ishlatish:**
```bash
python3 attendance_system.py
```

**Natija:** Xodim kelib ketganlari bazada saqlanadi

---

### 2. `register_employee.py` 👤 (XODIM QO'SHISH)
**Maqsadi:** Yangi xodimni vebkamadan qo'shish

- ✅ Xodimning ismini so'raydi
- ✅ Departamentni so'raydi
- ✅ Vebkamadan yuzni qayd qiladi
- ✅ Yuzning 128-bit kodini hisoblaydi
- ✅ Bazada saqlaydi

**Ishlatish:**
```bash
python3 register_employee.py
```

**Natija:** Xodim bazaga qo'shiladi

---

### 3. `database.py` 🗄️ (BAZA FUNKSIYALARI)
**Maqsadi:** MySQL baza bilan aloqa

**Funksiyalar:**
- `create_tables()` - 3 ta jadvalni yaratish
- `add_employee()` - Xodim qo'shish
- `record_attendance()` - Kelib ketish qaydiy
- `get_daily_attendance()` - Kunlik hisobi
- `get_attendance_report()` - Haftalik/oylik hisobi
- `get_attendance_log()` - Xodimning tarixi

**Faylni tahrirlash kerak emas!**

---

### 4. `reports.py` 📊 (HISOBOTLAR)
**Maqsadi:** Davomat hisobotlarini ko'rish

**Menyu:**
1. **Kunlik davomat** - kim kelib, kim ketgan
2. **Haftalik hisobi** - keldi, kech keldi, o'rtacha vaqt
3. **Xodim tarixi** - bitta xodimning 7 kunlik kelib ketishi
4. **Chiqish**

**Ishlatish:**
```bash
python3 reports.py
```

**Natija:** Jadvallı hisobotlar ekranda ko'rsatiladi

---

### 5. `setup_database.py` 🔧 (BAZA O'RNATISH)
**Maqsadi:** MySQL bazani va jadvalni yaratish

- ✅ `bank_attendance` bazasini yaratadi
- ✅ 3 ta jadvalni yaratadi (employees, attendance, attendance_log)
- ✅ Faqat bir marta ishlatiladi

**Ishlatish:**
```bash
python3 setup_database.py
```

---

## ⚙️ KONFIGURATSIYA FAYLLAR

### 6. `.env.example` ⚙️
**Maqsadi:** MySQL konfiguratsiya shabloni

```
DB_HOST=localhost      # MySQL serveri
DB_USER=root           # MySQL foydalanuvchi
DB_PASSWORD=           # Parol
DB_NAME=bank_attendance
```

**Qilish kerak:** `.env` nomiga o'zgartiring va parolni to'ldiring

---

### 7. `requirements.txt` 📦
**Maqsadi:** Python kutubxonalari

```
opencv-python==4.8.1.78           # Video/kamera
face-recognition==1.3.5            # Yuz taniş
numpy==1.24.3                      # Sonli hisob
Pillow==10.0.0                     # Rasm qayta ishlash
mysql-connector-python==8.2.0      # MySQL ulanish
python-dotenv==1.0.0               # .env o'qish
```

**O'rnatish:**
```bash
pip install -r requirements.txt
```

---

## 📚 QOIDANOMA VA QILAVARI

### 8. `README_DAVOMAT.md` 📖 (ASOSIY QOIDANOMA)
**Maqsadi:** To'liq qo'llanma (Oz'bek tilida)

- Loyiha tarkibi
- O'rnatish qadam-qadam
- Foydalanish ko'rsatmasi
- Muammolar va yechimlar
- SQL so'rovlar
- Xavfsizlik

---

### 9. `SETUP.md` 🛠️ (O'RNATISH QILAVARI)
**Maqsadi:** Tezkor o'rnatish 5 daqiqada

- Tezkor qadam-qadam
- MySQL o'rnatish (Linux/Mac/Windows)
- Tekshirish buyruqlari
- Tezkor yechimlar

---

## 🚀 ILOVA FAYLLAR

### 10. `quickstart.py` ⚡ (TEZKOR MENYU)
**Maqsadi:** Interaktiv menyu bilan boshlanish

**Nima qiladi:**
- Python versiyasini tekshirish
- MySQL tekshirish
- Kutubxonalarni tekshirish
- `.env` yaratish
- Menyu bilan programlarni ishlatish

**Ishlatish:**
```bash
python3 quickstart.py
```

---

### 11. `FAYL_TUSHUNTIRISHI.md` 📄 (BU FAYL)
**Maqsadi:** Barcha fayllarning tushuntirishi

---

## 📂 FAYLNING TARKIBI

```
face_recognition_system/
│
├── 🎥 ASOSIY DASTURLAR
│   ├── attendance_system.py      ← Davomat tizimi (vebkamera)
│   ├── register_employee.py      ← Xodim qo'shish
│   ├── reports.py                ← Hisobotlar
│   └── setup_database.py         ← Baza o'rnatish
│
├── 🔧 YORDAMCHI KODLAR
│   ├── database.py               ← MySQL funksiyalari
│   ├── utils.py                  ← Yuzlarni qayta ishlash (eski)
│   ├── main.py                   ← Sodda taniş (eski)
│   └── register.py               ← Sodda qo'shish (eski)
│
├── ⚙️ KONFIGURATSIYA
│   ├── .env.example              ← MySQL konfiguratsiya
│   ├── requirements.txt           ← Python kutubxonalari
│   └── .env                      ← Siz yaratadigan fayl
│
├── 📚 QOIDANOMA
│   ├── README_DAVOMAT.md         ← Asosiy qoidanoma
│   ├── README.md                 ← Eski qoidanoma
│   ├── SETUP.md                  ← O'rnatish qilavari
│   └── FAYL_TUSHUNTIRISHI.md    ← Bu fayl
│
└── 🚀 ILOVA
    └── quickstart.py             ← Tezkor boshlanish menyu
```

---

## 🔄 ISHLATISH TARTIBILI

### Birinchi marta (Bir vaqt):
```
1. pip install -r requirements.txt    (Kutubxonalar)
2. cp .env.example .env              (Konfiguratsiya)
3. nano .env                         (Paroli to'ldirish)
4. python3 setup_database.py         (Baza yaratish)
5. python3 register_employee.py      (Xodim qo'shish)
```

### Har kunlik:
```
python3 attendance_system.py         (Davomat qo'shish)
python3 reports.py                   (Hisobotlarni ko'rish)
```

---

## 📊 BAZA JADVALLARI

### 1. `employees` (Xodimlar)
```
id | name | face_encoding | department | position | status | created_at
```

### 2. `attendance` (Kunlik davomat)
```
id | employee_id | entry_time | exit_time | date | status | notes
```

### 3. `attendance_log` (Barcha kelib ketishlar)
```
id | employee_id | timestamp | action | confidence
```

---

## 🎯 QISQACHA TARIF

| Fayl | Nima qiladi | Qachon ishlatamiz |
|------|-----------|------------------|
| `attendance_system.py` | Yuzni taniydi va qayd qiladi | **HAR KUN** |
| `register_employee.py` | Yangi xodim qo'shadi | **Yangi odam kelib qo'lganda** |
| `reports.py` | Hisobotlarni ko'rsatadi | **Axşom yoki report kerak bo'lganda** |
| `setup_database.py` | Bazani yaratadi | **Faqat bir marta!** |
| `quickstart.py` | Menyu bilan boshlanish | **Birinchi marta yoki o'rnatish** |
| `.env` | MySQL parol va ma'lumotlari | **Konfiguratsiya uchun** |

---

## ✅ JORIY HOLAT

### TAYYOR FAYLLAR ✓
- [x] `attendance_system.py` - To'liq dastur
- [x] `register_employee.py` - Xodim qo'shish
- [x] `database.py` - MySQL funksiyalari
- [x] `reports.py` - Hisobotlar
- [x] `setup_database.py` - Baza o'rnatish
- [x] `quickstart.py` - Tezkor menyu
- [x] `.env.example` - Konfiguratsiya
- [x] `requirements.txt` - Kutubxonalar
- [x] `README_DAVOMAT.md` - Qoidanoma
- [x] `SETUP.md` - O'rnatish qilavari
- [x] `FAYL_TUSHUNTIRISHI.md` - Bu fayl

---

## 🚀 BOSHLASH

### Tezkor (5 daqiqa):
```bash
python3 quickstart.py
```

### Yoki step-by-step:
```bash
# 1. Kutubxonalar
pip install --break-system-packages -r requirements.txt

# 2. Konfiguratsiya
cp .env.example .env
nano .env  # Parol yozing

# 3. Baza
python3 setup_database.py

# 4. Xodim
python3 register_employee.py

# 5. Davomat
python3 attendance_system.py
```

---

**✅ BARCHA TAYYOR! ISHGA TUSHIRING! 🎉**
