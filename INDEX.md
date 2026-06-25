# 📑 BANK XODIM DAVOMAT TIZIMI - FAYLLAR INDEKSI

## 🚀 BOSHLANG!

### Eng tezkor yo'l (1 minuta):
```bash
python3 quickstart.py
```

### Yoki step-by-step (5 minuta):
1. `START.md` - O'qing (3 qadam)
2. `python3 setup_database.py` - Baza yarating
3. `python3 register_employee.py` - Xodim qo'shing
4. `python3 attendance_system.py` - Ishlatish

---

## 📚 FAYLLAR RO'YXATI

### 🎥 ASOSIY DASTURLAR
| Fayl | Nima qiladi | Qachon |
|------|-----------|--------|
| `attendance_system.py` | Vebkama + Davomat | **HAR KUN** |
| `register_employee.py` | Xodim qo'shish | Yangi odam |
| `reports.py` | Hisobotlar | Axşom |
| `setup_database.py` | Baza yaratish | **BIR MARTA** |

### 🔧 TEXNIK FAYLLAR
| Fayl | Maqsadi |
|------|--------|
| `database.py` | SQLite baza funksiyalari |
| `utils.py` | Yuz qayta ishlash |
| `main.py` | Sodda taniş (eski) |
| `register.py` | Sodda qo'shish (eski) |

### ⚙️ KONFIGURATSIYA
| Fayl | Nima |
|------|------|
| `bank_attendance.db` | SQLite baza fayli |
| `requirements.txt` | Kutubxonalar |

### 📖 QOIDANOMALAR
| Fayl | Maqsadi | Vaziyi |
|------|--------|--------|
| `START.md` | Birdan boshlanish | ⭐ **BOSHLANG SHUDAN** |
| `SETUP.md` | O'rnatish qadam-qadam | Tafsiliy |
| `README_DAVOMAT.md` | To'liq qoidanoma | **ENG KATTA** |
| `FAYL_TUSHUNTIRISHI.md` | Barcha fayllar | Texnik |
| `LOYIHANING_XULASASI.txt` | Xulosa | Qisqa |
| `INDEX.md` | Bu fayl | Indeks |

### 🚀 ILOVA
| Fayl | Nima |
|------|------|
| `quickstart.py` | Interaktiv menyu |

---

## 🎯 HARAKAT-REJA

### ✅ Birinchi marta (o'rnatish)
```
1. START.md - o'qing
2. pip install -r requirements.txt
3. python3 setup_database.py
4. python3 register_employee.py (xodim qo'shing)
```

### ✅ Har kun
```
1. python3 attendance_system.py
2. python3 reports.py (agar kerak bo'lsa)
```

---

## 📊 BAZA TUZILISHI

```
bank_attendance/
├── employees
│   ├── id (PRIMARY KEY)
│   ├── name
│   ├── face_encoding (BLOB)
│   ├── department
│   ├── position
│   └── status (active/inactive)
│
├── attendance
│   ├── id
│   ├── employee_id (FK)
│   ├── entry_time
│   ├── exit_time
│   ├── date
│   └── status (present/late/absent)
│
└── attendance_log
    ├── id
    ├── employee_id (FK)
    ├── timestamp
    ├── action (entry/exit)
    └── confidence
```

---

## ❓ KO'P BERILADIGAN SAVOLLAR

### "Qaydan boshlash kerak?"
→ **`START.md`** o'qing yoki `python3 quickstart.py` ishlatish

### "MySQL kerakmi?"
→ Yo'q. Loyiha hozir SQLite bilan ishlaydi va `bank_attendance.db` faylidan foydalanadi.

### "Xodim qanday qo'shiladi?"
→ `python3 register_employee.py`

### "Vebkamada yuz tanilmadi"
→ `README_DAVOMAT.md` - MUAMMOLAR BO'LIMI

### "Barcha fayllar nima qiladi?"
→ `FAYL_TUSHUNTIRISHI.md`

---

## 🔗 FAYLLAR ULANISHI

```
quickstart.py (MENU)
    ├─→ setup_database.py (Baza yaratish)
    ├─→ register_employee.py (Xodim qo'shish)
    │   └─→ database.py
    ├─→ attendance_system.py (Asosiy)
    │   ├─→ database.py
    │   └─→ utils.py
    └─→ reports.py (Hisobotlar)
        └─→ database.py

Konfiguratsiya:
    bank_attendance.db → setup_database.py yaratadi
    requirements.txt → pip install
```

---

## 📈 ISHLATISH STATISTIKASI

| Dastur | Chastotasi | Vaqti |
|--------|----------|------|
| `attendance_system.py` | **HAR KUN** | 8 soat+ |
| `register_employee.py` | Rar (yangi odam) | 2 minuta |
| `reports.py` | Axşom/haftalik | 10 minuta |
| `setup_database.py` | **BIR MARTA** | 1 minuta |

---

## ✨ XUSUSIYATLAR

- ✅ Real-time yuz taniş
- ✅ Vebkamadan avtomatik kelib ketish qaydiy
- ✅ SQLite bazada saqlash
- ✅ Kunlik/haftalik hisobotlar
- ✅ Admin bilan to'g'rilash (SQL)
- ✅ Xavfli ma'lumotlar (code, rasm emas)

---

## 🚀 HOZIR BOSHLANG!

### Eng tezkor:
```bash
cd /home/kamronbek/Desktop/face_recognition_system
python3 quickstart.py
```

### Yoki:
```bash
cat START.md
```

---

**🎉 LOYIHA 100% TAYYOR! BOSHLANG! 🎉**
