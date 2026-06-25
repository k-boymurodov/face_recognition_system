"""
🏦 Bank Davomat - Telegram Bot
Xodimlarning kelib ketgani Telegram orqali xabar yuborish
"""

import os
import html
from datetime import datetime, timedelta
import logging
from database import get_daily_attendance, get_all_employees, get_attendance_log
import json
from urllib import request, error
from utils import read_input

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

# Konfiguratsiya
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def is_telegram_configured():
    """Telegram token va chat id sozlanganini tekshirish."""
    return bool(
        TELEGRAM_BOT_TOKEN
        and CHAT_ID
        and TELEGRAM_BOT_TOKEN != "your_bot_token_here"
        and CHAT_ID != "your_chat_id_here"
    )


def send_telegram_message(text):
    """Telegram'ga xabar yuborish."""
    if not is_telegram_configured():
        logging.warning("Telegram sozlanmagan: TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID kerak.")
        return False

    try:
        telegram_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            telegram_api,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with request.urlopen(req, timeout=5) as response:
            response_text = response.read().decode("utf-8")

        if response.status == 200:
            return True

        logging.error(f"Telegram xatosi: {response_text}")
        return False
    except error.HTTPError as e:
        logging.error(f"Telegram xatosi: {e.read().decode('utf-8')}")
        return False
    except error.URLError as e:
        logging.error(f"Telegram ulanish xatosi: {e}")
        return False
    except Exception as e:
        logging.error(f"Telegram xatosi: {e}")
        return False


def send_telegram_photo(photo_bytes, caption):
    """Telegram'ga rasm va caption yuborish."""
    if not is_telegram_configured():
        print("⚠️ Telegram sozlanmagan: TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID kerak.")
        logging.warning("Telegram sozlanmagan: TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID kerak.")
    if not photo_bytes:
        return send_telegram_message(caption)

    try:
        boundary = "----BankAttendanceBoundary"
        telegram_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

        fields = {
            "chat_id": CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
        }
        body = bytearray()

        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            b'Content-Disposition: form-data; name="photo"; filename="attendance.jpg"\r\n'
        )
        body.extend(b"Content-Type: image/jpeg\r\n\r\n")
        body.extend(photo_bytes)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = request.Request(
            telegram_api,
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )

        with request.urlopen(req, timeout=10) as response:
            response_text = response.read().decode("utf-8")

        if response.status == 200:
            return True

        logging.error(f"Telegram rasm xatosi: {response_text}")
        return False
    except error.HTTPError as e:
        logging.error(f"Telegram rasm xatosi: {e.read().decode('utf-8')}")
        return False
    except error.URLError as e:
        logging.error(f"Telegram ulanish xatosi: {e}")
        return False
    except Exception as e:
        logging.error(f"Telegram rasm xatosi: {e}")
        return False


def send_unknown_person_alert(photo_bytes):
    """Noma'lum shaxs haqida ogohlantirish yuborish."""
    time_str = datetime.now().strftime("%H:%M:%S")
    date_str = datetime.now().strftime('%d.%m.%Y')
    
    caption = f"""
<b>⚠️ DIQQAT: NOMA'LUM SHAXS!</b>

Bank hududida ro'yxatdan o'tmagan shaxs aniqlandi.

<b>⏰ Vaqt:</b> {time_str}
<b>📅 Sana:</b> {date_str}
"""
    
    if send_telegram_photo(photo_bytes, caption):
        logging.warning("Noma'lum shaxs haqida ogohlantirish yuborildi.")
        return True
    return False


def send_daily_attendance():
    """Kunlik davomat hisobini Telegram'ga yuborish."""
    print("\n📊 Kunlik davomat Telegram'ga yuborilmoqda...")
    logging.info("Kunlik davomat Telegram'ga yuborilmoqda...")
    records = get_daily_attendance()
    
    if not records:
        message = "❌ Shu kunning qaydlari yo'q!"
        send_telegram_message(message)
        return
    
    today = datetime.now().strftime("%d.%m.%Y")
    
    message = f"""
<b>📊 KUNLIK DAVOMAT HISOBI</b>
<b>Sana:</b> {today}
<b>Vaqt:</b> {datetime.now().strftime('%H:%M:%S')}

"""
    
    keldi_count = 0
    for record in records:
        name = html.escape(record['name'] if record['name'] else "Qaydlanmadi")
        dept = html.escape(record['department'] if record['department'] else "-")
        entry = record['entry_time'].strftime("%H:%M") if record['entry_time'] else "-"
        exit_t = record['exit_time'].strftime("%H:%M") if record['exit_time'] else "-"
        
        if entry != "-":
            keldi_count += 1
            status_emoji = "✅" if exit_t != "-" else "🚪"
            message += f"{status_emoji} <b>{name}</b> ({dept})\n"
            message += f"   🚪 Kelib: {entry}   🏠 Ketdi: {exit_t}\n\n"
    
    message += f"\n<b>Jami:</b> {keldi_count} ta xodim keldi"
    
    if send_telegram_message(message):
        logging.info("Telegram'ga yubordi!")
    else:
        logging.error("Yuborilmadi")


def send_attendance_notification(name, action, confidence, photo_bytes=None):
    """Xodim kelib ketgani xabar qilish."""
    emoji = "🚪 KELIB" if action == "entry" else "🏠 KETGAN"
    time_str = datetime.now().strftime("%H:%M:%S")
    safe_name = html.escape(name)
    
    message = f"""
<b>{emoji} ✓</b>

<b>👤 Xodim:</b> {safe_name}
<b>⏰ Vaqt:</b> {time_str}
<b>🎯 Aniqlik:</b> {confidence:.1f}%
<b>📅 Sana:</b> {datetime.now().strftime('%d.%m.%Y')}
"""
    
    if send_telegram_photo(photo_bytes, message):
        logging.info(f"{name} - {emoji} (Telegram'ga yubordi)")
        return True
    return False


def send_employee_history(name):
    """Xodimning kelib ketish tarixini Telegram'ga yuborish."""
    from database import get_employee_by_name
    
    employee = get_employee_by_name(name)
    if not employee:
        message = f"❌ '{name}' xodim topilmadi!"
        send_telegram_message(message)
        return
    
    logs = get_attendance_log(employee['id'], days=7)
    
    if not logs:
        message = f"❌ {name} uchun qaydlar yo'q!"
        send_telegram_message(message)
        return
    
    safe_name = html.escape(name)
    department = html.escape(employee['department'] or "-")
    position = html.escape(employee['position'] or "-")

    message = f"""
<b>📋 XODIM KELIB KETISH TARIXI</b>

<b>👤 Xodim:</b> {safe_name}
<b>🏢 Departament:</b> {department}
<b>💼 Lavozim:</b> {position}

<b>So'nggi 7 kunlik kelib ketishlar:</b>
"""
    
    for log in logs[:10]:  # Oxirgi 10 ta qayd
        timestamp = log['timestamp'].strftime("%Y-%m-%d %H:%M") if log['timestamp'] else "-"
        action = "🚪 KELIB" if log['action'] == 'entry' else "🏠 KETGAN"
        confidence = log['confidence'] if log['confidence'] else 0
        
        message += f"\n{action} {timestamp} ({confidence:.0f}%)"
    
    send_telegram_message(message)


def send_weekly_report():
    """Haftalik hisobini Telegram'ga yuborish."""
    from database import get_attendance_report
    
    start_date = (datetime.now() - timedelta(days=7)).date()
    end_date = datetime.now().date()
    
    report = get_attendance_report(start_date, end_date)
    
    if not report:
        message = "❌ Haftalik qaydlar yo'q!"
        send_telegram_message(message)
        return
    
    message = f"""
<b>📈 HAFTALIK DAVOMAT HISOBI</b>
<b>Davr:</b> {start_date} dan {end_date} gacha

<b>Xodimlar:</b>
"""
    
    for record in report:
        name = html.escape(record['name'] if record['name'] else "Noma'lum")
        keldi = record['keldi'] if record['keldi'] else 0
        kech = record['kech_keldi'] if record['kech_keldi'] else 0
        avg_time = record['orta_vaqt'] if record['orta_vaqt'] else 0
        
        message += f"\n👤 <b>{name}</b>"
        message += f"\n   ✅ Keldi: {keldi} kun"
        message += f"\n   ⏰ Kech keldi: {kech} kun"
        message += f"\n   ⏱️ O'rtacha: {avg_time:.1f} soat\n"
    
    send_telegram_message(message)


def show_menu():
    """Telegram menyu."""
    message = """
<b>🏦 BANK XODIM DAVOMAT TIZIMI</b>

<b>Buyruqlar:</b>
/kunlik - Kunlik davomat
/haftalik - Haftalik hisobi
/oqib - Xodimning kelib ketish tarixi
/xodimlar - Barcha xodimlar
/start - Boshlanish
"""
    send_telegram_message(message)


if __name__ == "__main__":
    print("\n" + "="*60)
    logging.info("🔔 TELEGRAM BOT - DAVOMAT XABARLARI")
    print("="*60)
    
    if is_telegram_configured():
        logging.info(f"Token: {TELEGRAM_BOT_TOKEN[:10]}...")
        logging.info(f"Chat ID: {CHAT_ID}")
    else:
        logging.warning("Telegram sozlanmagan.")
        logging.warning(".env fayliga TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID yozing.")

    print("\n📌 MENYU:")
    print("   1. Kunlik davomat yuborish")
    print("   2. Haftalik hisobi yuborish")
    print("   3. Xodimning tarixi")
    print("   4. Barcha xodimlarni ko'rish")
    print("   5. Test xabari")
    
    choice = read_input("Variantni tanlang (1-5): ")
    if choice is None:
        choice = ""
    
    if choice == "1":
        send_daily_attendance()
    elif choice == "2":
        send_weekly_report()
    elif choice == "3":
        name = read_input("Xodimning ismini kiriting: ")
        if name:
            send_employee_history(name)
    elif choice == "4":
        emps = get_all_employees()
        msg = "<b>📋 BARCHA XODIMLAR</b>\n\n"
        for emp in emps:
            name = html.escape(emp['name'])
            department = html.escape(emp['department'] or "-")
            msg += f"👤 {name} ({department})\n"
        send_telegram_message(msg)
    elif choice == "5":
        test_msg = f"""
<b>✅ TEST XABARI</b>

Bot to'g'ri ishlaydi!
⏰ Vaqt: {datetime.now().strftime('%H:%M:%S')}
📅 Sana: {datetime.now().strftime('%d.%m.%Y')}
"""
        send_telegram_message(test_msg)
    
    print("\n✅ Yakunlandi!")
    logging.info("Yakunlandi!")
