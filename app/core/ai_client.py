import os
from typing import Union

from dotenv import load_dotenv

from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError, AuthenticationError


# تحميل متغيرات البيئة من ملف .env
load_dotenv()


def ask_ai(input_data: Union[str, list[dict]]) -> str:
    """
    تستقبل الدالة:
    - نص واحد بعد فلترة البيانات الحساسة
    - أو قائمة رسائل تمثل المحادثة

    الهدف: إرسال النص الآمن إلى مزود الذكاء الاصطناعي.
    """

    # تحديد مزود الذكاء الاصطناعي من ملف .env
    provider = os.getenv("AI_PROVIDER", "dummy").lower().strip()

    # إذا كان المزود OpenAI نرسل الطلب له
    if provider == "openai":
        return _ask_openai(input_data)

    # الرد الافتراضي إذا لم يتم تفعيل OpenAI
    return _ask_dummy(input_data)

def _ask_dummy(input_data: Union[str, list[dict]]) -> str:
    # رد تجريبي بدون الاتصال بمزود AI حقيقي
    if isinstance(input_data, list):
        last_user_message = ""

        # استخراج آخر رسالة من المستخدم
        for message in reversed(input_data):
            if message.get("role") == "user":
                last_user_message = message.get("content", "")
                break

        return (
            "Dummy AI response: Conversation messages were received after privacy filtering. "
            f"Last user message: {last_user_message}"
        )

    return (
        "Dummy AI response: The text was received after privacy filtering. "
        "Set AI_PROVIDER=openai in the .env file to enable the real AI provider."
    )


def _build_system_instruction() -> str:
    # تعليمات ثابتة للـ AI عشان يتعامل مع البيانات المقنعة بشكل صحيح
    return (
        "You are SecurePipe's secure AI assistant. "
        "Your primary goal is to help the user normally, clearly, and professionally. "

        "The user request has already passed through SecurePipe's privacy filtering layer before reaching you. "
        "This means sensitive data may already be replaced with placeholders. "

        "The request may contain placeholders such as: "
        "[EMAIL], [PHONE], [NATIONAL_ID], [IQAMA_ID], [PASSPORT], [DATE_OF_BIRTH], "
        "[ADDRESS], [FAMILY_DATA], [IBAN], [BANK_ACCOUNT], [CARD_PAN], [CVV], "
        "[BANK_STATEMENT], [INCOME_DATA], [DEBT_DATA], [INVESTMENT_DATA], "
        "[PASSWORD], [OTP], [LOGIN_CODE], [IP_ADDRESS], and [MAC_ADDRESS]. "

        "The request may also contain Arabic placeholders such as: "
        "[البريد_الإلكتروني], [رقم_الجوال], [رقم_الهوية], [رقم_الإقامة], [رقم_الجواز], "
        "[تاريخ_الميلاد], [العنوان], [بيانات_العائلة], [الآيبان], [رقم_الحساب], "
        "[رقم_البطاقة], [رمز_CVV], [كشف_حساب], [بيانات_الدخل], [بيانات_الديون], "
        "[بيانات_الاستثمار], [كلمة_المرور], [رمز_التحقق], and [رمز_الدخول]. "

        "Treat all placeholders as neutral protected tokens. "
        "Do not refuse to help only because the message contains placeholders or sensitive-data markers. "
        "Do not focus your answer on the fact that the data was masked unless the user directly asks about privacy or security. "
        "Continue solving the user's actual request using the safe masked content. "

        "If the user asks you to write, rewrite, summarize, analyze, translate, explain, troubleshoot, classify, "
        "compare, draft an email, draft a letter, review a document, or answer questions about uploaded content, "
        "perform the task normally and keep the placeholders unchanged. "

        "Never attempt to reconstruct, infer, guess, complete, or reveal the original hidden values behind placeholders. "
        "Never ask the user to provide passwords, OTP codes, CVV numbers, full bank card numbers, full bank account numbers, "
        "national ID numbers, iqama numbers, passport numbers, or other sensitive data. "

        "Do not add new sensitive fields, sensitive labels, or sensitive placeholders that were not required by the user's request. "
        "For example, do not add fields such as phone number, national ID, passport number, IBAN, bank account number, "
        "card number, CVV, password, OTP, address, or date of birth unless the user explicitly requested that such a field "
        "must appear in the output or it is strictly necessary for the requested document format. "

        "When drafting forms, letters, emails, templates, or official messages, keep the output minimal and relevant to the user's request. "
        "Avoid adding unnecessary personal-data fields. "
        "If a placeholder is already present in the user's request, you may preserve it where relevant. "
        "If a sensitive placeholder is not needed to complete the task, omit it. "

        "Only refuse or warn strongly if the user explicitly asks you to expose, recover, reconstruct, bypass, misuse, "
        "or share sensitive information. "

        "If the user asks how SecurePipe protects data, explain that SecurePipe masks sensitive information before sending "
        "the request to the AI provider, and that the AI receives only the safe payload. "

        "Answer in the same language as the user's request whenever possible. "
        "If the user writes in Arabic, answer in Arabic. If the user writes in English, answer in English. "
        "Keep the response practical, useful, and direct."
    )


def _convert_messages_to_text(messages: list[dict]) -> str:
    """
    Converts conversation history into one plain text input.

    Important security rule:
    - User messages coming here should already be sanitized by SecurePipe.
    - Do not send original sensitive text to the AI provider.
    """

    # تجهيز المحادثة كنص واحد قبل إرسالها للـ AI
    conversation_lines = []

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        # تجاهل الرسائل الفارغة
        if not content or not str(content).strip():
            continue

        # حفظ دور كل رسالة داخل النص النهائي
        if role == "assistant":
            conversation_lines.append(f"Assistant: {content}")
        else:
            conversation_lines.append(f"User: {content}")

    return "\n\n".join(conversation_lines)


def _ask_openai(input_data: Union[str, list[dict]]) -> str:
    # قراءة إعدادات OpenAI من ملف .env
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    # التأكد من وجود مفتاح OpenAI
    if not api_key or api_key == "PUT_YOUR_OPENAI_API_KEY_HERE":
        return "AI configuration error: OPENAI_API_KEY is missing in the .env file."

    # إنشاء عميل OpenAI
    client = OpenAI(api_key=api_key)

    try:
        # تحويل المحادثة إلى نص إذا كان الإدخال قائمة رسائل
        if isinstance(input_data, list):
            openai_input = _convert_messages_to_text(input_data)
        else:
            openai_input = input_data

        # إرسال النص الآمن إلى نموذج ChatGPT
        response = client.responses.create(
            model=model_name,
            instructions=_build_system_instruction(),
            input=openai_input,
        )

        return response.output_text or "AI returned an empty response."

    except AuthenticationError as error:
        # خطأ في مفتاح OpenAI
        return (
            "OpenAI authentication error. Please check OPENAI_API_KEY in the .env file. "
            f"Technical detail: {str(error)}"
        )

    except RateLimitError as error:
        # تجاوز الحد أو مشكلة في الرصيد
        return (
            "OpenAI rate limit or quota error. Please check your OpenAI billing, quota, or usage limits. "
            "Your sensitive data was still protected because only the sanitized text was prepared for AI processing. "
            f"Technical detail: {str(error)}"
        )

    except APITimeoutError as error:
        # انتهاء مهلة الاتصال
        return (
            "OpenAI request timed out. Please try again. "
            "Your sensitive data was still protected because only the sanitized text was prepared for AI processing. "
            f"Technical detail: {str(error)}"
        )

    except APIError as error:
        # خطأ عام من OpenAI API
        return (
            "OpenAI API error occurred. "
            "Your sensitive data was still protected because only the sanitized text was prepared for AI processing. "
            f"Technical detail: {str(error)}"
        )

    except Exception as error:
        # أي خطأ غير متوقع
        return (
            "Unexpected OpenAI integration error occurred. "
            "Your sensitive data was still protected because only the sanitized text was prepared for AI processing. "
            f"Technical detail: {str(error)}"
        )