import logging
import os
from datetime import datetime

def setup_logging():
    """Global logging konfiguratsiyasini sozlash."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = datetime.now().strftime("app_%Y-%m-%d.log")
    log_filepath = os.path.join(log_dir, log_filename)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler() # Konsolga ham chiqarish
        ]
    )
    # Ba'zi kutubxonalar loglarini kamaytirish
    logging.getLogger('face_recognition').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)

    logging.info("Logging tizimi ishga tushirildi.")