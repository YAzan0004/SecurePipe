import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


# تحديد مجلد حفظ ملفات الإثبات
EVIDENCE_DIR = Path("evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)


# حفظ إثبات عملية الفلترة لكل طلب
def save_evidence(
    original_text: str,
    sanitized_text: str,
    detected: Dict[str, int],
    sensitive_types: List[str],
    has_sensitive_data: bool,
    request_id: str,
) -> str:
    now = datetime.now()

    # وقت مخصص لاسم الملف عشان ما تتكرر الأسماء
    created_at_for_file = now.strftime("%Y%m%d_%H%M%S_%f")

    # وقت واضح داخل ملف JSON
    created_at_for_display = now.strftime("%Y-%m-%d %H:%M:%S")

    # إنشاء اسم ومسار ملف الإثبات
    file_name = f"evidence_{created_at_for_file}.json"
    file_path = EVIDENCE_DIR / file_name

    # تجهيز بيانات الإثبات للحفظ
    evidence_payload = {
        "metadata": {
            "request_id": request_id,
            "timestamp": created_at_for_display,
            "project": "SecurePipe-New",
            "version": "1.0.0"
        },
        "privacy_control": {
            "original_text_sent_to_ai": False,
            "ai_input_source": "sanitized_text",
            "sensitive_data_masked_before_ai": has_sensitive_data
        },
        "detection_summary": detected,
        "content": {
            "original_text": original_text,
            "sanitized_text": sanitized_text,
            "sensitive_types": sensitive_types,
            "has_sensitive_data": has_sensitive_data
        },
        "ai_payload": {
            "sent_to_ai": sanitized_text
        }
    }

    # كتابة ملف الإثبات بصيغة JSON
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(evidence_payload, file, ensure_ascii=False, indent=4)

    # إرجاع مسار ملف الإثبات
    return str(file_path)