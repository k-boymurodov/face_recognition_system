#!/usr/bin/env python3
"""
⚡ Tezkor Boshlanish (Quick Start)
Bank Xodim Davomat Tizimi
"""

import os
import subprocess
import sys
import importlib
from pathlib import Path
import logging


def print_header():
    """Sarlavhani chop etish."""
    # setup_logging() main funksiyasida chaqiriladi

    logging.info("="*70)
    logging.info("🏦 BANK XODIM DAVOMAT TIZIMI - TEZKOR BOSHLANISH")
    logging.info("="*70)

def check_venv():
    """Virtual environment faolligini tekshirish."""
    if sys.prefix != sys.base_prefix:
        logging.info("   ✅ Virtual environment (venv) - FAOL")
        return True
    else:
        logging.error("   ❌ Virtual environment faol emas!")
        logging.info("   💡 Ishga tushirish: source venv/bin/activate")
        return False

def check_python():
    """Python versiyasini tekshirish."""
    logging.info("1️⃣ Python versiyasini tekshirish...")
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info >= (3, 8):
        logging.info(f"   ✅ Python {py_version} - OK")
        return True
    else:
        logging.error(f"   ❌ Python {py_version} (3.8+ kerak)")
        return False

def check_database():
    """SQLite baza faylini tekshirish."""
    logging.info("2️⃣ SQLite baza tekshiruvi...")
    try:
        from database import DB_FILE
        if Path(DB_FILE).exists():
            logging.info(f"   ✅ Baza mavjud: {Path(DB_FILE).name}")
        else:
            logging.warning("   ⚠️ Baza hali yaratilmagan")
            logging.info("   💡 Menyudan 1-variantni tanlab setup qiling")
    except (ImportError, Exception):
        logging.warning("   ⚠️ Baza ma'lumotlarini (DB_FILE) o'qib bo'lmadi.")
        return


def check_requirements():
    """Kutubxonalarni tekshirish."""
    logging.info("3️⃣ Python kutubxonalarini tekshirish...")
    try:
        modules = [
            ('cv2', 'opencv-python'),
            ('numpy', 'numpy'),
            ('dlib', 'dlib'),
            ('face_recognition_models', 'face_recognition_models (git)'),
            ('face_recognition', 'face-recognition'),
            ('PIL.Image', 'Pillow'),
            ('gtts', 'gTTS'),
            ('pygame', 'pygame'),
            ('pyaudio', 'pyaudio')
        ]
        
        missing = []
        for mod_name, pkg_name in modules:
            try:
                importlib.import_module(mod_name)
            except ImportError:
                missing.append(pkg_name)

        if missing:
            raise ImportError(f"Yetishmayotgan paketlar: {', '.join(missing)}")

        logging.info("   ✅ Barcha kutubxonalar va AI modellari mavjud")
        return True
    except ImportError as e:
        logging.error(f"   ❌ Kutubxona topilmadi: {e}")
        logging.info("   💡 MUAMMONI HAL QILISH:")
        logging.info("      1. Terminalda: source venv/bin/activate")
        logging.info("      2. Kutubxonalarni o'rnatish: pip install -r requirements.txt")
        logging.info("      3. Agar AI modellari topilmasa: pip install git+https://github.com/ageitgey/face_recognition_models")
        logging.info("      4. Agar internet ulanishida Error 128 chiqsa, proxy yoki tarmoq xavfsizligini tekshiring.")
        return False


def print_menu():
    """Asosiy menyu."""
    try:
        from utils import read_input
    except ImportError:
        logging.error("❌ 'utils.py' yuklanmadi. Kutubxonalarni o'rnatib qayta urinib ko'ring.")
        return

    while True:
        print("\n" + "="*70)
        print("🚀 KEYINGI QADAM")
        print("="*70)
        print("1. 🔧 Bazani o'rnatish (SETUP)")
        print("2. 👤 Xodim ro'yxatga olish")
        print("3. 🎥 Davomat tizimini ishlatish")
        print("4. 📊 Hisobotlarni ko'rish")
        print("5. 📚 Qo'llanmani ko'rish")
        print("6. ❌ Chiqish")
        print("="*70)
        
        choice = read_input("\nVariantni tanlang (1-6): ")
        if choice is None: # logging.info
            break
        
        if choice == "1":
            logging.info("🔧 Bazani o'rnatmoqda...")
            subprocess.run([sys.executable, "setup_database.py"])
            print("\n✅ Baza tayyor.")
        elif choice == "2":
            logging.info("👤 Xodim ro'yxatga olish...")
            subprocess.run([sys.executable, "register_employee.py"])
        elif choice == "3":
            logging.info("🎥 Davomat tizimini ishlatish...")
            try:
                subprocess.run([sys.executable, "attendance_system.py"])
            except KeyboardInterrupt:
                print("\n🛑 Tizim to'xtatildi.")
        elif choice == "4":
            logging.info("📊 Hisobotlarni ko'rish...")
            subprocess.run([sys.executable, "reports.py"])
        elif choice == "5":
            logging.info("📚 Qo'llanma...")
            subprocess.run(["cat", "README_DAVOMAT.md"])
        elif choice == "6":
            logging.info("Chiqilmoqda...")
            break
        elif choice:
            logging.warning("Noto'g'ri variant!")


def main():
    """Asosiy funksiya."""
    try:
        from logging_config import setup_logging
        setup_logging()
    except ImportError:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print_header()
    
    # Tekshiruvlar
    if not check_python():
        return
    
    if not check_venv():
        return

    check_database()
    
    if not check_requirements():
        logging.warning("⚠️ Ayrim kutubxonalar yetishmayapti!")
    
    logging.info("="*70)
    logging.info("✅ BARCHA TEKSHIRUVLAR TUGALLANDI!")
    logging.info("="*70)
    
    print_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Bekor qilindi.")
    except Exception as e:
        logging.error(f"Xato: {e}")
