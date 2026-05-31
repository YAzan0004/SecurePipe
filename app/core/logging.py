import logging
from pathlib import Path


# تحديد مجلد حفظ السجلات
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# تحديد ملف السجل الرئيسي
LOG_FILE = LOG_DIR / "securepipe.log"


# إعداد نظام التسجيل
def setup_logging():
    logger = logging.getLogger("securepipe")
    logger.setLevel(logging.INFO)

    # منع تكرار الـ handlers إذا تم استدعاء الدالة أكثر من مرة
    if logger.handlers:
        return logger

    # تنسيق شكل الرسائل داخل السجل
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # حفظ السجلات داخل ملف
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # عرض السجلات في شاشة التشغيل
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# كائن السجل المستخدم في المشروع
logger = setup_logging()