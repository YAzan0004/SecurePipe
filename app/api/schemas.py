from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional


# نموذج طلب معالجة النص
class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text submitted by the user")
    user_id: Optional[int] = None

    conversation_id: Optional[int] = None


# نموذج الاستجابة بعد معالجة النص
class ProcessResponse(BaseModel):
    original_text: str
    sanitized_text: str
    detected: Dict[str, int]
    sensitive_types: List[str]
    has_sensitive_data: bool
    ai_response: str
    evidence_file: str

    conversation_id: Optional[int] = None

    message_id: Optional[int] = None


# نموذج بيانات التسجيل
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


# نموذج بيانات تسجيل الدخول
class LoginRequest(BaseModel):
    username: str
    password: str


# نموذج بيانات المستخدم في الرد
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


# نموذج استجابة التسجيل أو الدخول
class AuthResponse(BaseModel):
    message: str
    user: UserResponse


# نموذج إنشاء محادثة
class ConversationCreateRequest(BaseModel):
    title: Optional[str] = "New Conversation"


# نموذج بيانات المحادثة
class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str

    class Config:
        from_attributes = True


# نموذج بيانات الرسالة
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str

    class Config:
        from_attributes = True