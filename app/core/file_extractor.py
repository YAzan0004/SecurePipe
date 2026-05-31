from io import BytesIO
from docx import Document
import pdfplumber


# أنواع الملفات المسموح برفعها
ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# استخراج النص من الملف حسب نوعه
def extract_text_from_bytes(file_bytes: bytes, content_type: str) -> str:
    if content_type not in ALLOWED_TYPES:
        raise ValueError("Unsupported file type. Only PDF, TXT, and DOCX are allowed.")

    # استخراج النص من ملف TXT
    if content_type == "text/plain":
        return _extract_txt(file_bytes)

    # استخراج النص من ملف PDF
    if content_type == "application/pdf":
        return _extract_pdf(file_bytes)

    # استخراج النص من ملف DOCX
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(file_bytes)

    raise ValueError("Unsupported file type.")


# قراءة ملفات TXT مع دعم أكثر من ترميز
def _extract_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


# استخراج النص من صفحات PDF
def _extract_pdf(file_bytes: bytes) -> str:
    extracted_pages = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text)

    return "\n\n".join(extracted_pages)


# استخراج النص من فقرات DOCX
def _extract_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)