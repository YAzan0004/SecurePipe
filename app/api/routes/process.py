import json
import re
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import ProcessRequest, ProcessResponse
from app.core.sanitizers import sanitize_text
from app.core.evidence import save_evidence
from app.core.ai_client import ask_ai
from app.core.file_extractor import ALLOWED_TYPES, extract_text_from_bytes
from app.core.database import get_db, User, Conversation, Message


# راوتر خاص بمعالجة النصوص والملفات
router = APIRouter(
    prefix="/process",
    tags=["Process"]
)


# عناوين افتراضية يتم استبدالها بعدين  
GENERIC_TITLES = {
    "New Secure Chat",
    "New Conversation",
    "First Secure AI Chat",
    "New Chat",
    "Secure Conversation",
    "File Analysis Request",
}


# إعدادات خاصة بتاريخ المحادثة والعنوان
MAX_HISTORY_MESSAGES = 10
MAX_TITLE_LENGTH = 42
MAX_TITLE_WORDS = 6
MAX_TITLE_SOURCE_CHARS = 900


# كلمات تدل على أسطر قد تحتوي بيانات حساسة
SENSITIVE_LINE_KEYWORDS = {
    "name", "full name", "email", "mobile", "phone", "national id", "id number",
    "iqama", "passport", "address", "iban", "card", "cvv", "password", "otp",
    "الاسم", "البريد", "الإيميل", "الايميل", "الجوال", "الهاتف", "رقم الهوية",
    "الهوية", "الإقامة", "الاقامة", "الجواز", "العنوان", "الآيبان", "الايبان",
    "البطاقة", "رمز التحقق", "كلمة المرور",
}


# التحقق هل النص عربي
def is_arabic_text(text: str) -> bool:
    return any("\u0600" <= char <= "\u06FF" for char in text or "")


# استخراج رسالة المستخدم من النص المدمج مع الملف
def extract_user_message_from_combined_text(text: str) -> str:
    """
    If the request came from /process/with-file, the text has this structure:

    User message:
    ...

    Uploaded file name:
    ...

    Extracted file text:
    ...

    For titles, we prefer the user's direct message and avoid using the full file content.
    """

    content = text or ""

    if "User message:" in content and "Uploaded file name:" in content:
        user_part = content.split("User message:", 1)[1].split("Uploaded file name:", 1)[0]
        user_part = user_part.strip()
        if user_part:
            return user_part

    return content.strip()


# تنظيف النص المستخدم لتوليد عنوان المحادثة
def remove_sensitive_title_context(text: str) -> str:
    """
    Removes obvious sensitive-data lines and sanitizer placeholders before generating a title.
    This keeps conversation titles useful without exposing personal details in the sidebar.
    """

    content = extract_user_message_from_combined_text(text)

    # إزالة الـ placeholders من العنوان
    content = re.sub(r"\[[A-Z_]+\]", " ", content)

    safe_lines = []

    for line in content.splitlines():
        line_clean = " ".join(line.strip().split())
        if not line_clean:
            continue

        lowered = line_clean.lower()

        # تجاهل الأسطر الحساسة إلا إذا كانت تحتوي طلب واضح
        if any(keyword in lowered for keyword in SENSITIVE_LINE_KEYWORDS):
            action_words = [
                "renew", "how", "request", "book", "explain", "summarize", "translate",
                "solve", "analyze", "write", "create", "compare", "calculate",
                "تجديد", "كيف", "ابي", "أبي", "اريد", "أريد", "اشرح", "لخص",
                "ترجم", "ترجمة", "حل", "حلل", "اكتب", "سو", "قارن", "احسب",
            ]

            if not any(action_word.lower() in lowered for action_word in action_words):
                continue

        safe_lines.append(line_clean)

    cleaned = " ".join(safe_lines)

    # إزالة الأرقام الطويلة من العنوان
    cleaned = re.sub(r"\b\d{4,}\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:،,.\n\t")

    return cleaned


# تنظيف العنوان النهائي وتقصيره
def clean_generated_title(title: str) -> str:
    """
    Cleans the AI-generated title and enforces sidebar-safe formatting.
    """

    clean_title = (title or "").strip()

    clean_title = clean_title.replace("\n", " ")
    clean_title = clean_title.replace("\r", " ")
    clean_title = clean_title.strip("\"'`“”‘’")
    clean_title = re.sub(r"\[[A-Z_]+\]", " ", clean_title)
    clean_title = re.sub(r"\b\d{4,}\b", " ", clean_title)
    clean_title = re.sub(r"\s+", " ", clean_title).strip(" -:،,.")

    words = clean_title.split()

    # تقليل عدد كلمات العنوان
    if len(words) > MAX_TITLE_WORDS:
        clean_title = " ".join(words[:MAX_TITLE_WORDS])

    # تقليل طول العنوان
    if len(clean_title) > MAX_TITLE_LENGTH:
        clean_title = clean_title[:MAX_TITLE_LENGTH].rstrip() + "..."

    return clean_title.strip(" -:،,.")


# التأكد أن العنوان لا يحتوي بيانات حساسة
def title_contains_sensitive_pattern(title: str) -> bool:
    """
    Blocks titles that accidentally contain sensitive-looking values.
    """

    content = title or ""

    patterns = [
        r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
        r"\b(?:\+?966|0)?5\d{8}\b",
        r"\b[12]\d{9}\b",
        r"\b[A-Z]{1,2}\d{6,9}\b",
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
        r"\b\d{4,}\b",
        r"\[[A-Z_]+\]",
    ]

    return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)


# عنوان احتياطي إذا فشل توليد العنوان بالذكاء الاصطناعي
def fallback_conversation_title(text: str) -> str:
    """
    Safe fallback when AI title generation fails.
    It creates a short title from the cleaned request without relying on fixed topic rules.
    """

    safe_text = remove_sensitive_title_context(text)

    if not safe_text:
        return "Secure Conversation"

    title = clean_generated_title(safe_text)

    if not title:
        return "Secure Conversation"

    if title_contains_sensitive_pattern(title):
        return "Secure Conversation"

    return title


# توليد عنوان ذكي للمحادثة باستخدام AI
def generate_ai_conversation_title(text: str) -> str | None:
    """
    Generates a smart title using the configured AI provider.
    The source text must already be sanitized before reaching this function.
    """

    safe_text = remove_sensitive_title_context(text)

    if not safe_text:
        return None

    safe_text = safe_text[:MAX_TITLE_SOURCE_CHARS]

    language_instruction = (
        "اكتب العنوان بالعربية إذا كان طلب المستخدم عربيًا."
        if is_arabic_text(safe_text)
        else "Write the title in English if the user request is in English."
    )

    # برومبت مخصص لتوليد عنوان قصير وآمن
    title_prompt = f"""
You are generating a sidebar title for a secure AI chat conversation.

Task:
Create a short, clear conversation title based on the user's request.

Rules:
- Return only the title.
- Maximum {MAX_TITLE_WORDS} words.
- Do not include names, emails, phone numbers, IDs, addresses, IBANs, card numbers, passwords, OTPs, or any personal data.
- Do not mention placeholders like [EMAIL], [PHONE], [NATIONAL_ID], or [ADDRESS].
- Do not use generic titles unless the topic is unclear.
- The title should describe the actual topic or task.
- {language_instruction}

User request:
{safe_text}
""".strip()

    try:
        ai_title = ask_ai([
            {
                "role": "system",
                "content": (
                    "You generate short safe conversation titles only. "
                    "Return only the title with no explanation."
                ),
            },
            {
                "role": "user",
                "content": title_prompt,
            },
        ])

        cleaned_title = clean_generated_title(ai_title)

        if not cleaned_title:
            return None

        if title_contains_sensitive_pattern(cleaned_title):
            return None

        generic_bad_titles = {
            "title",
            "conversation title",
            "secure conversation",
            "new conversation",
            "عنوان المحادثة",
            "محادثة آمنة",
            "محادثة جديدة",
        }

        if cleaned_title.lower() in generic_bad_titles and len(safe_text.split()) > 3:
            return None

        return cleaned_title

    except Exception:
        return None


# توليد عنوان المحادثة النهائي
def generate_conversation_title(text: str) -> str:
    """
    Generates a smart and safe sidebar title.

    Main behavior:
    - Uses AI to summarize the actual user topic into a short title.
    - Uses sanitized text only.
    - Falls back to a safe extractive title if AI generation fails.
    """

    ai_title = generate_ai_conversation_title(text)

    if ai_title:
        return ai_title

    return fallback_conversation_title(text)


# بناء تنبيه الخصوصية إذا تم اكتشاف بيانات حساسة
def build_sensitive_data_notice(original_text: str, sensitive_types: list[str]) -> str:
    if not sensitive_types:
        return ""

    if is_arabic_text(original_text):
        return (
            "\n\nتنبيه خصوصية: رسالتك كانت تحتوي على معلومات حساسة، "
            "وقام SecurePipe بحجبها قبل إرسال الطلب إلى الذكاء الاصطناعي. "
            "لا تشارك بيانات مثل رقم الهوية، الإقامة، الجواز، كلمات المرور، "
            "رموز التحقق، أرقام البطاقات البنكية، CVV، الآيبان، أو العنوان التفصيلي "
            "مع أي جهة غير موثوقة."
        )

    return (
        "\n\nPrivacy Notice: Your message contained sensitive information, "
        "and SecurePipe masked it before sending the request to the AI. "
        "Do not share data such as national IDs, iqama numbers, passports, passwords, "
        "OTP codes, card numbers, CVV, IBANs, or detailed addresses with untrusted parties."
    )


# جلب محادثة موجودة أو إنشاء محادثة جديدة
def get_or_create_conversation(
    db: Session,
    user_id: int | None,
    conversation_id: int | None,
    title_source_text: str,
):
    """
    Gets the existing conversation or creates a new one.

    Important:
    - If user_id is None, the system will not save messages in the database.
    - If conversation_id is provided, it must belong to the same user.
    - Conversation titles are generated from sanitized/safe text, not raw sensitive input.
    """

    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    conversation = None
    smart_title = generate_conversation_title(title_source_text)

    # التحقق من المحادثة إذا تم إرسال conversation_id
    if conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found for this user."
            )

        # تحديث العنوان إذا كان لا يزال افتراضيًا
        if conversation.title in GENERIC_TITLES:
            conversation.title = smart_title
            db.commit()
            db.refresh(conversation)

    # إنشاء محادثة جديدة إذا لم توجد
    if conversation is None:
        conversation = Conversation(
            user_id=user_id,
            title=smart_title,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation


# جلب آخر رسائل المحادثة لإرسال السياق للـ AI
def get_conversation_history(
    db: Session,
    conversation_id: int | None,
    limit: int = MAX_HISTORY_MESSAGES,
) -> list[dict]:
    """
    Returns the latest conversation messages in OpenAI/Ollama chat format:

    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]

    Security rule:
    - For user messages, we use sanitized_text only.
    - We do not send original_text back to the AI.
    """

    if conversation_id is None:
        return []

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )

    messages = list(reversed(messages))

    history = []

    for message in messages:
        if message.role == "user":
            content = message.sanitized_text or ""
        elif message.role == "assistant":
            content = message.response_text or ""
        else:
            continue

        if content.strip():
            history.append({
                "role": message.role,
                "content": content,
            })

    return history


# بناء قائمة الرسائل التي سترسل للـ AI
def build_ai_messages(
    history: list[dict],
    current_sanitized_text: str,
) -> list[dict]:
    """
    Builds the full message list sent to the AI.

    The current user message is appended after the previous history.
    """

    messages = history.copy()

    messages.append({
        "role": "user",
        "content": current_sanitized_text,
    })

    return messages


# إرسال المحادثة إلى مزود الذكاء الاصطناعي
def ask_ai_with_conversation(messages: list[dict]) -> str:
    """
    Sends the conversation to the AI.

    This assumes app.core.ai_client.ask_ai can accept a list of messages.
    """

    return ask_ai(messages)


# حفظ رسالة المستخدم ورد المساعد في قاعدة البيانات
def save_message_to_database(
    db: Session,
    conversation: Conversation | None,
    original_text: str,
    sanitized_text: str,
    ai_response: str,
    has_sensitive_data: bool,
    sensitive_types: list[str],
    evidence_file: str,
    request_id: str,
):
    """
    Saves both user and assistant messages.

    Returns:
    - conversation_id
    - user_message_id
    """

    if conversation is None:
        return None, None

    # حفظ رسالة المستخدم
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        original_text=original_text,
        sanitized_text=sanitized_text,
        response_text=None,
        has_sensitive_data=has_sensitive_data,
        sensitive_types=json.dumps(sensitive_types, ensure_ascii=False),
        evidence_file=evidence_file,
        request_id=request_id,
    )

    # حفظ رد الذكاء الاصطناعي
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        original_text=None,
        sanitized_text=None,
        response_text=ai_response,
        has_sensitive_data=False,
        sensitive_types=json.dumps([], ensure_ascii=False),
        evidence_file=evidence_file,
        request_id=request_id,
    )

    conversation.updated_at = datetime.utcnow()

    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)

    return conversation.id, user_message.id


# معالجة النص العادي بدون ملف
@router.post("/", response_model=ProcessResponse)
def process_text(
    request_body: ProcessRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    request_id = request.state.request_id
    original_text = request_body.text

    # فلترة النص من البيانات الحساسة
    sanitized_text, detected, sensitive_types, has_sensitive_data = sanitize_text(original_text)

    # حفظ ملف الإثبات
    evidence_file = save_evidence(
        original_text=original_text,
        sanitized_text=sanitized_text,
        detected=detected,
        sensitive_types=sensitive_types,
        has_sensitive_data=has_sensitive_data,
        request_id=request_id,
    )

    # جلب أو إنشاء المحادثة
    conversation = get_or_create_conversation(
        db=db,
        user_id=request_body.user_id,
        conversation_id=request_body.conversation_id,
        title_source_text=sanitized_text,
    )

    # جلب سياق المحادثة السابق
    history = get_conversation_history(
        db=db,
        conversation_id=conversation.id if conversation else None,
    )

    # بناء الرسائل المرسلة للـ AI
    ai_messages = build_ai_messages(
        history=history,
        current_sanitized_text=sanitized_text,
    )

    # إرسال النص الآمن للذكاء الاصطناعي
    ai_response = ask_ai_with_conversation(ai_messages)

    # إضافة تنبيه خصوصية إذا وجد بيانات حساسة
    privacy_notice = build_sensitive_data_notice(
        original_text=original_text,
        sensitive_types=sensitive_types,
    )

    ai_response = ai_response + privacy_notice

    # حفظ الرسائل في قاعدة البيانات
    conversation_id, message_id = save_message_to_database(
        db=db,
        conversation=conversation,
        original_text=original_text,
        sanitized_text=sanitized_text,
        ai_response=ai_response,
        has_sensitive_data=has_sensitive_data,
        sensitive_types=sensitive_types,
        evidence_file=evidence_file,
        request_id=request_id,
    )

    return ProcessResponse(
        original_text=original_text,
        sanitized_text=sanitized_text,
        detected=detected,
        sensitive_types=sensitive_types,
        has_sensitive_data=has_sensitive_data,
        ai_response=ai_response,
        evidence_file=evidence_file,
        conversation_id=conversation_id,
        message_id=message_id,
    )


# معالجة نص مع ملف مرفوع
@router.post("/with-file", response_model=ProcessResponse)
async def process_text_with_file(
    request: Request,
    message: str = Form(""),
    user_id: int | None = Form(None),
    conversation_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    request_id = request.state.request_id

    # التحقق من نوع الملف
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF, TXT, and DOCX are allowed."
        )

    file_bytes = await file.read()

    try:
        # استخراج النص من الملف
        extracted_text = extract_text_from_bytes(
            file_bytes=file_bytes,
            content_type=file.content_type,
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract text from file: {str(error)}"
        )

    # دمج رسالة المستخدم مع محتوى الملف
    combined_text = (
        f"User message:\n{message}\n\n"
        f"Uploaded file name:\n{file.filename}\n\n"
        f"Extracted file text:\n{extracted_text}"
    )

    # فلترة النص المدمج
    sanitized_text, detected, sensitive_types, has_sensitive_data = sanitize_text(combined_text)

    # حفظ ملف الإثبات
    evidence_file = save_evidence(
        original_text=combined_text,
        sanitized_text=sanitized_text,
        detected=detected,
        sensitive_types=sensitive_types,
        has_sensitive_data=has_sensitive_data,
        request_id=request_id,
    )

    # تجهيز مصدر آمن لعنوان المحادثة
    title_source_text = message.strip() if message and message.strip() else f"Analyze uploaded file: {file.filename}"
    sanitized_title_source, _, _, _ = sanitize_text(title_source_text)

    conversation = get_or_create_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        title_source_text=sanitized_title_source,
    )

    history = get_conversation_history(
        db=db,
        conversation_id=conversation.id if conversation else None,
    )

    ai_messages = build_ai_messages(
        history=history,
        current_sanitized_text=sanitized_text,
    )

    # إرسال محتوى الملف بعد الفلترة للذكاء الاصطناعي
    ai_response = ask_ai_with_conversation(ai_messages)

    privacy_notice = build_sensitive_data_notice(
        original_text=combined_text,
        sensitive_types=sensitive_types,
    )

    ai_response = ai_response + privacy_notice

    # حفظ نتيجة المعالجة في قاعدة البيانات
    saved_conversation_id, message_id = save_message_to_database(
        db=db,
        conversation=conversation,
        original_text=combined_text,
        sanitized_text=sanitized_text,
        ai_response=ai_response,
        has_sensitive_data=has_sensitive_data,
        sensitive_types=sensitive_types,
        evidence_file=evidence_file,
        request_id=request_id,
    )

    return ProcessResponse(
        original_text=combined_text,
        sanitized_text=sanitized_text,
        detected=detected,
        sensitive_types=sensitive_types,
        has_sensitive_data=has_sensitive_data,
        ai_response=ai_response,
        evidence_file=evidence_file,
        conversation_id=saved_conversation_id,
        message_id=message_id,
    )