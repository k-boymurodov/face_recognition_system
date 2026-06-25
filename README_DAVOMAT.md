# 🏦 Bank Xodim Davomat Tizimi

**Vebkamera orqali bank xodimlarini taniş qilib davomat bazaga saqlash tizimi.**

---

## 📋 Loyiha Tarkibi

| Fayl | Maqsadi |
|------|---------|
| **attendance_system.py** | 🎥 Asosiy dastur - vebkamera + davomat qa'ydi |
| **register_employee.py** | 📝 Yangi xodim qo'shish |
| **database.py** | 🗄️ SQLite baza funksiyalari |
| **reports.py** | 📊 Davomat hisobotlari |
| **setup_database.py** | 🔧 Baza yo o'rnatish |
| **requirements.txt** | 📦 Python kutubxonalari |
| **README.md** | 📚 Qo'llanma (bu fayl) |

---

## 🔧 O'rnatish

### 1️⃣ Kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

**Zarur kutubxonalar:**
- `opencv-python` - Video/kamera
- `face-recognition` - Yuz taniş (dlib-based)
- `numpy`, `Pillow` - Rasm qayta ishlash

### 2️⃣ Bazani yaratish:

```bash
python3 setup_database.py
```

**Chiqish:**
```
✅ SETUP MUVAFFAQIYATLI TUGALLANDI!
```

---

## 🚀 FOYDALANISH

### **1. 👤 Xodim ro'yxatga olish:**

```bash
python3 register_employee.py
```

**Qadam-qadam:**
1. Xodimning to'liq ismini kiriting
2. Departament (iختiyoriy)
3. Lavozim (iختiyoriy)
4. Vebkameraga 2-3 sekund qilib turgur
5. Dastur avtomatik yuzni 15 kadriga oladi
6. ✅ Muvaffaqiyatli saqlandi!

**Ma'lumot bazada saqlanadi:**
- Yuzning 128-o'lchamli kodi (face encoding)
- Xodimning shaxsiy ma'lumotlari
- Ro'yxatga olish sanasi

### **2. 🎥 Davomat tizimi (Asosiy):**

```bash
python3 attendance_system.py
```

**Nima qiladi:**
- Vebkameradan yuzni taniydi
- Xodim **kelib kelsa** - ✅ GREEN, "KELIB ✓"
- Xodim **ketishga harakat qilsa** - ✅ GREEN, "KETGAN ✗"
- Noma'lum odamlar - ❌ RED, "Noma'lum"
- **Bazaga avtomatik qayd** - entry_time, exit_time
- Kunlik hisobi ekranda ko'rsatiladi

**Chiqish:** `q` tugmasini bosing

### **3. 📊 Hisobotlarni ko'rish:**

```bash
python3 reports.py
```

**Menyu:**
1. **📊 Kunlik davomat** - Kim kelib ketgan (bugun yoki tanlangan sana)
2. **📈 Haftalik hisobi** - Keldi, kech keldi, o'rtacha vaqt
3. **📋 Xodim tarixi** - Bitta xodimning 7 kunlik kelib ketishi
4. **❌ Chiqish**

### **4. 🔔 Telegram xabarlari:**

1. Telegramda `@BotFather` orqali bot yarating va token oling.
2. Botga xabar yozing yoki kerakli guruhga botni qo'shing.
3. Chat ID ni oling.
4. `.env` fayl yarating:

```bash
cp .env.example .env
```

`.env` ichiga yozing:
```ini
TELEGRAM_BOT_TOKEN=botfather_bergan_token
TELEGRAM_CHAT_ID=sizning_chat_id
```

Test xabar yuborish:
```bash
python3 telegram_bot.py
```

Davomat ishlaganda xodim kelgan yoki ketgan paytda Telegramga avtomatik xabar boradi.

---

## 📊 Bazaning Jadvallari

### 1. `employees` - Xodimlar
```sql
SELECT * FROM employees;
```
| id | name | department | position | status | created_at |
|----|------|-----------|----------|--------|-----------|
| 1 | Ali Xo'jayev | IT | Manager | active | 2024-... |
| 2 | Zarrina | HR | Specialist | active | 2024-... |

### 2. `attendance` - Kunlik davomat
```sql
SELECT * FROM attendance WHERE date = DATE('now', 'localtime');
```
| id | employee_id | entry_time | exit_time | date | status |
|----|------------|-----------|----------|------|--------|
| 1 | 1 | 08:30:15 | 17:45:22 | 2024-06-09 | present |

### 3. `attendance_log` - Barcha kelib ketishlar
```sql
SELECT * FROM attendance_log ORDER BY timestamp DESC;
```
| id | employee_id | timestamp | action | confidence |
|----|------------|-----------|--------|-----------|
| 1 | 1 | 2024-06-09 08:30:15 | entry | 98.5 |
| 2 | 1 | 2024-06-09 17:45:22 | exit | 97.2 |

---

## 📈 Amaliy Misollar

### Misol 1: Bank boshidagi kamera
```bash
# Subaka 1: Xodimlarni o'rnatish (bir marta)
$ python3 register_employee.py
  # Ismingizni kiriting: Ali
  # ✅ Ali muvaffaqiyatli ro'yxatga olinidi!
  
  # Ismingizni kiriting: Zarrina  
  # ✅ Zarrina muvaffaqiyatli ro'yxatga olinidi!

# Subaka 2: Davomat (har kun)
$ python3 attendance_system.py
  # Ali KELIB ✓ 08:30:15
  # Zarrina KELIB ✓ 08:35:42
  # Ali KETGAN ✗ 17:45:30
  # ...

# Subaka 3: Hisobotlar (axşom)
$ python3 reports.py
  # Kunlik davomat bo'yicha:
  # Ali    08:30 → 17:45 | IT
  # Zarrina 08:35 → 17:50 | HR
```

---

## ⚙️ Parametrlar (Sozlash)

### `database.py` - Tolerance (aniqlik)
```python
tolerance = 0.6  # Yuzni taqqoslash darajasi
```
- **0.4 va kamroq** = Aniq (sezuvchan)
- **0.5-0.6** = O'rtacha (tavsiya)
- **0.7 va yuqori** = Qo'pol (ko'p xato)

### `attendance_system.py` - Ro'yxatga olish vaqti
```python
if (current_time - last_time).seconds > 10:
```
- 10 soniya ichida takrorlanmaydi
- Dinamik entry/exit aniqlash

---

## 🐛 Muammolar va Yechimlar

### ❌ Xodim tanilmadi
```bash
# 1. Yengi yuz qayd qiling: register_employee.py
# 2. Yetarli yorug'lik bo'lishi
# 3. Vebkama rawon ishlashi
```

### ❌ `bank_attendance.db` topilmadi
```bash
# Setup qayta o'tkazish:
python3 setup_database.py
```

---

## 📚 SQL So'rovlar (admin uchun)

### Har kim kelib ketgan?
```sql
SELECT e.name, a.date, a.entry_time, a.exit_time
FROM attendance a
JOIN employees e ON a.employee_id = e.id
ORDER BY a.date DESC, a.entry_time DESC;
```

### Kim hali ketmadi?
```sql
SELECT e.name, a.entry_time
FROM attendance a
JOIN employees e ON a.employee_id = e.id
WHERE a.date = DATE('now', 'localtime') AND a.exit_time IS NULL;
```

### Kech kelib etganlar (8:30 dan so'ng)
```sql
SELECT e.name, a.entry_time
FROM attendance a
JOIN employees e ON a.employee_id = e.id
WHERE a.date = DATE('now', 'localtime') AND TIME(a.entry_time) > '08:30:00';
```

---

## 🔒 Xavfsizlik

✅ **Salmoq kodlash** - Face encoding (128-bit vektor)
✅ **Takrorlashtiriladigan qayd** - Har kelib ketish qayd qilina
✅ **Editablе jadvali** - Admin uchun to'g'rilash imkonyati
✅ **Sura saqlash** - registered_faces/ papkasida

---

## 📞 Tez Yordam

| Muammo | Buyruq |
|--------|--------|
| Bazani qayta o'rnatish | `python3 setup_database.py` |
| Xodim qo'shish | `python3 register_employee.py` |
| Davomat ishlatish | `python3 attendance_system.py` |
| Hisobotlarni ko'rish | `python3 reports.py` |
| Xodimlarni ko'rish | `python3 -c "from database import get_all_employees; print(get_all_employees())"` |

---

**✅ Tayyor! Ishlatishni boshlang! 🚀**

**Muallif:** Bank Tizimi  
**Versiya:** 2.1 (SQLite + Davomat)  
**Til:** Uzbek (O'zbek)
