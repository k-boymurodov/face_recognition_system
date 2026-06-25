#!/usr/bin/env python3
"""
Setup script - Bazani va jadvalni yaratish
"""
import logging
from database import create_tables, db_connect


def setup_database():
    """Bazani yaratish."""
    from logging_config import setup_logging
    setup_logging()

    logging.info("="*60)
    logging.info("🔧 BANK DAVOMAT TIZIMI - SETUP")
    logging.info("="*60)
    
    logging.info("1️⃣ SQLite bazaga ulanish...")
    
    try:
        with db_connect() as conn:
            # db_connect() context manageri ulanishni o'zi boshqaradi
            pass
        if conn:
            logging.info("✅ Baza fayli tayyor!")
        else:
            logging.error("Baza ulanishda kutilmagan xato!")
            return False
    except Exception as e:
        logging.error(f"Baza ulanish xatosi: {e}")
        return False
    
    logging.info("2️⃣ Jadvallar yaratilmoqda...")
    
    if create_tables():
        logging.info("✅ Jadvalni muvaffaqiyatli yaratildi!")
    else:
        logging.error("Jadval yaratishda xato!")
        return False
    
    logging.info("="*60)
    logging.info("✅ SETUP MUVAFFAQIYATLI TUGALLANDI!")
    logging.info("="*60)
    logging.info("📌 Keyingi qadam:")
    logging.info("   python3 register_employee.py")
    logging.info("Yoki:")
    logging.info("   python3 attendance_system.py")
    logging.info("   python3 reports.py\n")
    
    return True


if __name__ == "__main__":
    setup_database()
