import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Header


# راوتر خاص بلوحة الإدارة
router = APIRouter(prefix="/admin", tags=["Admin"])


# مفتاح دخول الإدارة من .env أو قيمة افتراضية
ADMIN_KEY = os.getenv("ADMIN_KEY", "securepipe-admin-123")


# تحديد جذر المشروع
def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


# تحديد مسار قاعدة البيانات
def get_db_path() -> Path:
    return get_project_root() / "securepipe.db"


# تحديد مسار مجلد ملفات الإثبات
def get_evidence_dir() -> Path:
    return get_project_root() / "evidence"


# التحقق من مفتاح الإدارة قبل تنفيذ أي عملية إدارية
def verify_admin_key(x_admin_key: str | None) -> None:
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized admin access."
        )


# تنسيق التاريخ والوقت للعرض بتوقيت السعودية
def format_created_at(value) -> str:
    """
    Format datetime using Saudi Arabia local time UTC+3.

    Stored example:
    2026-05-29 04:20:38.135545

    Displayed example:
    2026-05-29 \\07:20
    """

    if value is None:
        return "-"

    value = str(value).strip()

    if not value:
        return "-"

    value_without_microseconds = value.split(".")[0]

    try:
        dt = datetime.fromisoformat(value_without_microseconds)
        saudi_dt = dt + timedelta(hours=3)

        date_part = saudi_dt.strftime("%Y-%m-%d")
        time_part = saudi_dt.strftime("%H:%M")

        return f"{date_part} \\{time_part}"

    except ValueError:
        pass

    if len(value_without_microseconds) >= 16:
        date_part = value_without_microseconds[:10]
        time_part = value_without_microseconds[11:16]
        return f"{date_part} \\{time_part}"

    return value_without_microseconds


# فتح اتصال بقاعدة البيانات
def get_connection():
    db_path = get_db_path()

    if not db_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Database file not found: {db_path}"
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# قراءة ملفات الإثبات وتجميع إحصائياتها
def get_evidence_summary() -> dict:
    """
    Reads evidence JSON files and returns monitoring statistics.

    Returns:
    - evidence_files_count
    - sensitive_requests_count
    - latest_evidence_file
    - latest_evidence_timestamp
    - most_detected_type
    - most_detected_type_count
    """

    evidence_dir = get_evidence_dir()

    if not evidence_dir.exists():
        return {
            "evidence_files_count": 0,
            "sensitive_requests_count": 0,
            "latest_evidence_file": "-",
            "latest_evidence_timestamp": "-",
            "most_detected_type": "-",
            "most_detected_type_count": 0
        }

    evidence_files = list(evidence_dir.glob("*.json"))

    if not evidence_files:
        return {
            "evidence_files_count": 0,
            "sensitive_requests_count": 0,
            "latest_evidence_file": "-",
            "latest_evidence_timestamp": "-",
            "most_detected_type": "-",
            "most_detected_type_count": 0
        }

    sensitive_requests_count = 0
    detected_totals: dict[str, int] = {}

    latest_file = max(evidence_files, key=lambda file: file.stat().st_mtime)
    latest_evidence_timestamp = "-"

    # المرور على ملفات الإثبات لحساب الإحصائيات
    for evidence_file in evidence_files:
        try:
            with open(evidence_file, "r", encoding="utf-8") as file:
                evidence_data = json.load(file)

            content = evidence_data.get("content", {})
            if content.get("has_sensitive_data") is True:
                sensitive_requests_count += 1

            detection_summary = evidence_data.get("detection_summary", {})
            for sensitive_type, count in detection_summary.items():
                try:
                    count_as_int = int(count)
                except (TypeError, ValueError):
                    count_as_int = 0

                detected_totals[sensitive_type] = (
                    detected_totals.get(sensitive_type, 0) + count_as_int
                )

            if evidence_file == latest_file:
                metadata = evidence_data.get("metadata", {})
                latest_evidence_timestamp = metadata.get("timestamp", "-")

        except (json.JSONDecodeError, OSError):
            continue

    most_detected_type = "-"
    most_detected_type_count = 0

    # تحديد أكثر نوع بيانات حساسة تم اكتشافه
    if detected_totals:
        most_detected_type, most_detected_type_count = max(
            detected_totals.items(),
            key=lambda item: item[1]
        )

        if most_detected_type_count == 0:
            most_detected_type = "-"

    return {
        "evidence_files_count": len(evidence_files),
        "sensitive_requests_count": sensitive_requests_count,
        "latest_evidence_file": latest_file.name,
        "latest_evidence_timestamp": latest_evidence_timestamp,
        "most_detected_type": most_detected_type,
        "most_detected_type_count": most_detected_type_count
    }


# إرجاع بيانات لوحة الإدارة
@router.get("/dashboard")
def get_admin_dashboard(x_admin_key: str | None = Header(default=None)):
    """
    Returns admin statistics without exposing password_hash.
    Requires X-Admin-Key header.
    """

    verify_admin_key(x_admin_key)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # حساب عدد المستخدمين والمحادثات والرسائل
        cursor.execute("SELECT COUNT(*) AS count FROM users;")
        users_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM conversations;")
        conversations_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM messages;")
        messages_count = cursor.fetchone()["count"]

        # جلب بيانات المستخدمين بدون إظهار password_hash
        cursor.execute("""
            SELECT
                id,
                username,
                email,
                created_at
            FROM users
            ORDER BY id DESC;
        """)

        users = []
        for row in cursor.fetchall():
            user = dict(row)
            user["created_at"] = format_created_at(user.get("created_at"))
            users.append(user)

        conn.close()

        evidence_summary = get_evidence_summary()

        return {
            "users_count": users_count,
            "conversations_count": conversations_count,
            "messages_count": messages_count,
            "users": users,
            "evidence": evidence_summary
        }

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )


# إرجاع آخر ملف إثبات
@router.get("/evidence/latest")
def get_latest_evidence(x_admin_key: str | None = Header(default=None)):
    """
    Returns the latest evidence JSON file content.
    Requires X-Admin-Key header.
    """

    verify_admin_key(x_admin_key)

    evidence_dir = get_evidence_dir()

    if not evidence_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="Evidence directory not found."
        )

    evidence_files = list(evidence_dir.glob("*.json"))

    if not evidence_files:
        raise HTTPException(
            status_code=404,
            detail="No evidence files found."
        )

    latest_file = max(evidence_files, key=lambda file: file.stat().st_mtime)

    try:
        with open(latest_file, "r", encoding="utf-8") as file:
            evidence_data = json.load(file)

        return {
            "file_name": latest_file.name,
            "evidence": evidence_data
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Latest evidence file is not a valid JSON file."
        )

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read latest evidence file: {str(error)}"
        )


# حذف مستخدم واحد مع بياناته المرتبطة
@router.delete("/users/{user_id}")
def delete_user(user_id: int, x_admin_key: str | None = Header(default=None)):
    """
    Deletes one user and all related conversations/messages.
    Requires X-Admin-Key header.
    """

    verify_admin_key(x_admin_key)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # التأكد أن المستخدم موجود
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?;", (user_id,))
        user = cursor.fetchone()

        if user is None:
            conn.close()
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )

        # حذف رسائل المستخدم أولًا
        cursor.execute("""
            DELETE FROM messages
            WHERE conversation_id IN (
                SELECT id FROM conversations WHERE user_id = ?
            );
        """, (user_id,))
        deleted_messages = cursor.rowcount

        # حذف محادثات المستخدم
        cursor.execute("""
            DELETE FROM conversations
            WHERE user_id = ?;
        """, (user_id,))
        deleted_conversations = cursor.rowcount

        # حذف المستخدم
        cursor.execute("""
            DELETE FROM users
            WHERE id = ?;
        """, (user_id,))
        deleted_users = cursor.rowcount

        conn.commit()
        conn.close()

        return {
            "message": "User and related data deleted successfully.",
            "deleted_user_id": user_id,
            "deleted_users": deleted_users,
            "deleted_conversations": deleted_conversations,
            "deleted_messages": deleted_messages
        }

    except HTTPException:
        raise

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )


# حذف جميع بيانات الاختبار وملفات الإثبات
@router.delete("/clear-test-data")
def clear_test_data(x_admin_key: str | None = Header(default=None)):
    """
    Deletes all users, conversations, messages, and evidence JSON files.
    Requires X-Admin-Key header.
    """

    verify_admin_key(x_admin_key)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # حذف كل الرسائل والمحادثات والمستخدمين
        cursor.execute("DELETE FROM messages;")
        deleted_messages = cursor.rowcount

        cursor.execute("DELETE FROM conversations;")
        deleted_conversations = cursor.rowcount

        cursor.execute("DELETE FROM users;")
        deleted_users = cursor.rowcount

        conn.commit()
        conn.close()

        # حذف ملفات الإثبات من مجلد evidence
        deleted_evidence_files = 0
        evidence_dir = get_evidence_dir()

        if evidence_dir.exists():
            for evidence_file in evidence_dir.glob("*.json"):
                try:
                    evidence_file.unlink()
                    deleted_evidence_files += 1
                except OSError:
                    continue

        return {
            "message": "All test data and evidence files deleted successfully.",
            "deleted_users": deleted_users,
            "deleted_conversations": deleted_conversations,
            "deleted_messages": deleted_messages,
            "deleted_evidence_files": deleted_evidence_files
        }

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )