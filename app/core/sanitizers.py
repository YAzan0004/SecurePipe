import re


# قائمة أنواع البيانات الحساسة التي يبحث عنها النظام
SENSITIVE_TYPES = [
    "email",
    "phone",
    "national_id",
    "iqama_id",
    "passport",
    "date_of_birth",
    "address",
    "family_data",
    "iban",
    "bank_account",
    "card_pan",
    "cvv",
    "bank_statement",
    "income_data",
    "debt_data",
    "investment_data",
    "password",
    "otp",
    "ip_address",
    "mac_address",
]


# تجهيز ملخص الكشف بقيم ابتدائية صفر
def _empty_detection_summary() -> dict[str, int]:
    return {sensitive_type: 0 for sensitive_type in SENSITIVE_TYPES}


# زيادة عداد نوع البيانات إذا تم اكتشافه
def _add_detection(detected: dict[str, int], sensitive_type: str, count: int) -> None:
    if count > 0:
        detected[sensitive_type] = detected.get(sensitive_type, 0) + count


# استبدال أي نمط حساس بالـ placeholder المناسب
def _replace_pattern(
    text: str,
    pattern: str,
    placeholder: str,
    sensitive_type: str,
    detected: dict[str, int],
    flags: int = re.IGNORECASE,
) -> str:
    updated_text, count = re.subn(pattern, placeholder, text, flags=flags)
    _add_detection(detected, sensitive_type, count)
    return updated_text


# استبدال القيم الحساسة التي تأتي بعد مسميات واضحة
def _replace_labeled_value(
    text: str,
    label_pattern: str,
    placeholder: str,
    sensitive_type: str,
    detected: dict[str, int],
    value_pattern: str = r"[^\n\r,;]+",
) -> str:
    """
    نبدل القيم الحساسة الي تطلع بعد مسميات عربية أو إنجليزية.
    مثال: البريد، الجوال، الهوية، الإقامة، الجواز، كلمة المرور، رمز التحقق.
    """

    # السماح بوجود فواصل بين المسمى والقيمة مثل : أو = أو هو
    separator_pattern = (
        r"\s*"
        r"(?:"
        r"[:：=]|"
        r"\-|–|—|"
        r"\bis\b|"
        r"\bare\b|"
        r"\bهو\b|"
        r"\bهي\b"
        r")?"
        r"\s*"
    )

    pattern = rf"({label_pattern})({separator_pattern})({value_pattern})"

    # الإبقاء على المسمى واستبدال القيمة فقط
    def replacer(match: re.Match) -> str:
        return f"{match.group(1)}{match.group(2)}{placeholder}"

    updated_text, count = re.subn(pattern, replacer, text, flags=re.IGNORECASE)
    _add_detection(detected, sensitive_type, count)
    return updated_text


# الدالة الرئيسية لتنظيف النص من البيانات الحساسة
def sanitize_text(text: str) -> tuple[str, dict[str, int], list[str], bool]:
    detected = _empty_detection_summary()

    if not text:
        return "", detected, [], False

    sanitized_text = text

    # ------------------------------------------------------------
    # Authentication secrets
    # ------------------------------------------------------------

    # إخفاء CVV إذا جاء بعد مسمى واضح
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:cvv|cvc|card security code|security code|"
            r"رمز\s*cvv|رمز\s*cvc|رمز\s*الأمان|رمز\s*امان|"
            r"الرقم\s*السري\s*للبطاقة|"
            r"رمز\s*بطاقتي|رمز\s*البطاقة|رمز\s*البطاقه)"
        ),
        placeholder="[CVV]",
        sensitive_type="cvv",
        detected=detected,
        value_pattern=r"\d{3,4}",
    )

    # إخفاء كلمات المرور إذا جاءت بعد مسمى واضح
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:login password|account password|password|passcode|"
            r"كلمة\s*المرور|كلمه\s*المرور|كلمة\s*مروري|كلمه\s*مروري|"
            r"الرقم\s*السري|رقمي\s*السري|كلمة\s*السر|كلمه\s*السر|"
            r"باسوردي|الباسورد|باسورد)"
        ),
        placeholder="[PASSWORD]",
        sensitive_type="password",
        detected=detected,
        value_pattern=r"[^\s,;،]+",
    )

    # إخفاء كلمة المرور المعقدة حتى لو بدون مسمى
    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=(
            r"(?<![\w@.\-])"
            r"(?=[^\s,;،]*[a-z])"
            r"(?=[^\s,;،]*[A-Z])"
            r"(?=[^\s,;،]*\d)"
            r"(?=[^\s,;،]*[^A-Za-z0-9\s,;،])"
            r"[^\s,;،]{8,}"
            r"(?![\w@.\-])"
        ),
        placeholder="[PASSWORD]",
        sensitive_type="password",
        detected=detected,
    )

    # إخفاء رموز التحقق
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:otp|one[-\s]?time password|verification code|login code|auth code|"
            r"رمز\s*التحقق|رمز\s*الدخول|كود\s*التحقق|كود\s*الدخول|"
            r"رمز\s*التوثيق|رمز\s*المصادقة|"
            r"رمزي|كودي|كودى|رمز\s*تحققي|كود\s*تحققي)"
        ),
        placeholder="[OTP]",
        sensitive_type="otp",
        detected=detected,
        value_pattern=r"\d{4,8}",
    )

    # ------------------------------------------------------------
    # Identity information
    # ------------------------------------------------------------

    # إخفاء البريد الإلكتروني إذا جاء بعد مسمى
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:email|e-mail|email address|mail|"
            r"البريد\s*الإلكتروني|البريد\s*الالكتروني|"
            r"الايميل|الإيميل|ايميل|إيميل|ايميلي|إيميلي|"
            r"بريدي\s*الإلكتروني|بريدي\s*الالكتروني|بريدي)"
        ),
        placeholder="[EMAIL]",
        sensitive_type="email",
        detected=detected,
        value_pattern=r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}",
    )

    # إخفاء أي بريد إلكتروني عام داخل النص
    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b",
        placeholder="[EMAIL]",
        sensitive_type="email",
        detected=detected,
    )

    # إخفاء رقم الجوال إذا جاء بعد مسمى
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:phone|mobile|mobile number|phone number|contact number|"
            r"رقم\s*الجوال|رقم\s*الهاتف|رقم\s*التواصل|الجوال|الهاتف|"
            r"رقم\s*جوالي|رقم\s*هاتفي|رقم\s*تواصلي|"
            r"جوالي|جوالى|هاتفي|هاتفى|رقمي|رقمى)"
        ),
        placeholder="[PHONE]",
        sensitive_type="phone",
        detected=detected,
        value_pattern=r"(?:\+966|00966|966|0)?[\s-]?5[\s-]?\d[\s-]?\d{3}[\s-]?\d{4}",
    )

    # إخفاء أرقام الجوال السعودية داخل النص
    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"(?<!\d)(?:\+966|00966|966|0)?[\s-]?5[\s-]?\d[\s-]?\d{3}[\s-]?\d{4}(?!\d)",
        placeholder="[PHONE]",
        sensitive_type="phone",
        detected=detected,
    )

    # إخفاء رقم الهوية الوطنية
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:national id|national identity|id number|identity number|"
            r"رقم\s*الهوية\s*الوطنية|رقم\s*الهوية|الهوية\s*الوطنية|"
            r"رقم\s*هويتي|رقم\s*هويتى|هويتي|هويتى|الهوية|هوية)"
        ),
        placeholder="[NATIONAL_ID]",
        sensitive_type="national_id",
        detected=detected,
        value_pattern=r"1\d{9}",
    )

    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"\b1\d{9}\b",
        placeholder="[NATIONAL_ID]",
        sensitive_type="national_id",
        detected=detected,
    )

    # إخفاء رقم الإقامة
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:iqama|iqama id|residency id|resident id|"
            r"رقم\s*الإقامة|رقم\s*الاقامة|الإقامة|الاقامة|"
            r"رقم\s*إقامتي|رقم\s*اقامتي|إقامتي|اقامتي|إقامتى|اقامتى)"
        ),
        placeholder="[IQAMA_ID]",
        sensitive_type="iqama_id",
        detected=detected,
        value_pattern=r"2\d{9}",
    )

    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"\b2\d{9}\b",
        placeholder="[IQAMA_ID]",
        sensitive_type="iqama_id",
        detected=detected,
    )

    # إخفاء رقم الجواز
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:passport|passport number|"
            r"رقم\s*جواز\s*السفر|رقم\s*الجواز|جواز\s*السفر|الجواز|"
            r"رقم\s*جوازي|رقم\s*جوازى|جوازي|جوازى)"
        ),
        placeholder="[PASSPORT]",
        sensitive_type="passport",
        detected=detected,
        value_pattern=r"[A-Z]{1,2}\d{6,9}",
    )

    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"\b[A-Z]{1,2}\d{6,9}\b",
        placeholder="[PASSPORT]",
        sensitive_type="passport",
        detected=detected,
    )

    # إخفاء تاريخ الميلاد
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:date of birth|birth date|dob|"
            r"تاريخ\s*الميلاد|تاريخ\s*الولادة|"
            r"تاريخ\s*ميلادي|تاريخ\s*ميلادى|الميلاد|ميلادي|ميلادى)"
        ),
        placeholder="[DATE_OF_BIRTH]",
        sensitive_type="date_of_birth",
        detected=detected,
        value_pattern=(
            r"(?:\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}|"
            r"\d{4}[\/\-.]\d{1,2}[\/\-.]\d{1,2})"
        ),
    )

    # إخفاء العنوان
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:home address|residential address|full address|"
            r"العنوان\s*السكني|العنوان\s*الوطني|موقع\s*السكن|"
            r"موقع\s*سكني|موقع\s*سكنى|العنوان|عنواني|عنوانى|"
            r"سكني|سكنى|موقعي|موقعى)"
        ),
        placeholder="[ADDRESS]",
        sensitive_type="address",
        detected=detected,
        value_pattern=r"[^\n\r]+",
    )

    # إخفاء بيانات العائلة
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:family member|family phone|family data|dependent data|"
            r"بيانات\s*الأسرة|بيانات\s*الاسرة|رقم\s*أحد\s*أفراد\s*الأسرة|"
            r"رقم\s*احد\s*افراد\s*الاسرة|بيانات\s*الأبناء|بيانات\s*الابناء|"
            r"بيانات\s*عائلتي|بيانات\s*عائلتى|عائلتي|عائلتى|"
            r"أسرتي|اسرتي|أسرتى|اسرتى)"
        ),
        placeholder="[FAMILY_DATA]",
        sensitive_type="family_data",
        detected=detected,
        value_pattern=r"[^,،.\n\r]+",
    )

    # ------------------------------------------------------------
    # Financial information
    # ------------------------------------------------------------

    # إخفاء رقم الآيبان
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:iban|bank iban|"
            r"رقم\s*الآيبان|رقم\s*الايبان|الآيبان|الايبان|"
            r"رقم\s*آيباني|رقم\s*ايباني|آيباني|ايباني|آيبانى|ايبانى)"
        ),
        placeholder="[IBAN]",
        sensitive_type="iban",
        detected=detected,
        value_pattern=r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}",
    )

    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
        placeholder="[IBAN]",
        sensitive_type="iban",
        detected=detected,
    )

    # إخفاء رقم الحساب البنكي
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:bank account number|bank account|account number|"
            r"رقم\s*الحساب\s*البنكي|رقم\s*الحساب|الحساب\s*البنكي|"
            r"حسابي\s*البنكي|حسابى\s*البنكي|رقم\s*حسابي|رقم\s*حسابى|"
            r"حسابي|حسابى)"
        ),
        placeholder="[BANK_ACCOUNT]",
        sensitive_type="bank_account",
        detected=detected,
        value_pattern=r"\d{8,24}",
    )

    # إخفاء رقم البطاقة البنكية إذا جاء بعد مسمى
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:card number|credit card|debit card|bank card|"
            r"البطاقة\s*البنكية|البطاقه\s*البنكية|رقم\s*البطاقة|رقم\s*البطاقه|"
            r"بطاقتي\s*البنكية|بطاقتى\s*البنكية|رقم\s*بطاقتي|رقم\s*بطاقتى|"
            r"بطاقتي|بطاقتى)"
        ),
        placeholder="[CARD_PAN]",
        sensitive_type="card_pan",
        detected=detected,
        value_pattern=r"(?:\d[ -]?){13,19}",
    )

    # إخفاء أرقام البطاقات داخل النص
    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
        placeholder="[CARD_PAN]",
        sensitive_type="card_pan",
        detected=detected,
    )

    # إخفاء بيانات كشف الحساب
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:bank statement|account statement|statement of account|"
            r"كشف\s*حسابي|كشف\s*حسابى|كشف\s*حساب\s*بنكي|"
            r"كشف\s*الحساب|كشف\s*حساب)"
        ),
        placeholder="[BANK_STATEMENT]",
        sensitive_type="bank_statement",
        detected=detected,
        value_pattern=r"[^,،.\n\r]+",
    )

    # إخفاء بيانات الدخل أو الراتب
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:monthly income|annual income|income|salary|"
            r"الدخل\s*الشهري|الدخل\s*السنوي|الدخل|الراتب|"
            r"دخلي\s*الشهري|دخلى\s*الشهري|دخلي|دخلى|راتبي|راتبى)"
        ),
        placeholder="[INCOME_DATA]",
        sensitive_type="income_data",
        detected=detected,
        value_pattern=r"[^,،.\n\r]+",
    )

    # إخفاء بيانات الديون والقروض
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:liabilities|debts|debt|loans|loan|"
            r"الالتزامات|الديون|الدين|القروض|القرض|"
            r"التزاماتي|التزاماتى|ديوني|ديونى|ديني|دينى|قرضي|قرضى)"
        ),
        placeholder="[DEBT_DATA]",
        sensitive_type="debt_data",
        detected=detected,
        value_pattern=r"[^,،.\n\r]+",
    )

    # إخفاء بيانات الاستثمارات والمحافظ
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:stock portfolio|investment portfolio|investments|investment|portfolio|"
            r"المحفظة\s*الاستثمارية|المحفظه\s*الاستثماريه|"
            r"محفظتي\s*الاستثمارية|محفظتى\s*الاستثمارية|"
            r"الاستثمارات|الاستثمار|استثماراتي|استثماراتى|"
            r"استثماري|استثمارى|محفظتي|محفظتى)"
        ),
        placeholder="[INVESTMENT_DATA]",
        sensitive_type="investment_data",
        detected=detected,
        value_pattern=r"[^,،.\n\r]+",
    )

    # ------------------------------------------------------------
    # Technical identifiers
    # ------------------------------------------------------------

    # إخفاء عنوان IP
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:ip address|ip|"
            r"عنوان\s*ip|عنوان\s*IP|الآي\s*بي|الاي\s*بي|آي\s*بي|اي\s*بي)"
        ),
        placeholder="[IP_ADDRESS]",
        sensitive_type="ip_address",
        detected=detected,
        value_pattern=r"(?:\d{1,3}\.){3}\d{1,3}",
    )

    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        placeholder="[IP_ADDRESS]",
        sensitive_type="ip_address",
        detected=detected,
    )

    # إخفاء عنوان MAC
    sanitized_text = _replace_labeled_value(
        text=sanitized_text,
        label_pattern=(
            r"(?:mac address|mac|"
            r"عنوان\s*mac|عنوان\s*MAC|الماك|ماك)"
        ),
        placeholder="[MAC_ADDRESS]",
        sensitive_type="mac_address",
        detected=detected,
        value_pattern=r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}",
    )

    sanitized_text = _replace_pattern(
        text=sanitized_text,
        pattern=r"\b(?:[0-9A-F]{2}:){5}[0-9A-F]{2}\b",
        placeholder="[MAC_ADDRESS]",
        sensitive_type="mac_address",
        detected=detected,
    )

    # استخراج الأنواع التي تم اكتشافها فقط
    sensitive_types = [
        sensitive_type
        for sensitive_type, count in detected.items()
        if count > 0
    ]

    # تحديد هل النص يحتوي على بيانات حساسة أم لا
    has_sensitive_data = len(sensitive_types) > 0

    return sanitized_text, detected, sensitive_types, has_sensitive_data