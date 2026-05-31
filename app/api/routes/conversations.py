from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import ConversationCreateRequest, ConversationResponse
from app.core.database import get_db, User, Conversation, Message


# راوتر خاص بإدارة المحادثات
router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


# إنشاء محادثة جديدة لمستخدم معيّن
@router.post("/{user_id}", response_model=ConversationResponse)
def create_conversation(
    user_id: int,
    request: ConversationCreateRequest,
    db: Session = Depends(get_db)
):
    # التأكد أن المستخدم موجود
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # إنشاء المحادثة بعنوان مخصص أو افتراضي
    new_conversation = Conversation(
        user_id=user_id,
        title=request.title or "New Conversation"
    )

    # حفظ المحادثة في قاعدة البيانات
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)

    return new_conversation


# جلب جميع محادثات مستخدم معيّن
@router.get("/user/{user_id}", response_model=list[ConversationResponse])
def get_user_conversations(
    user_id: int,
    db: Session = Depends(get_db)
):
    # التأكد أن المستخدم موجود
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # جلب المحادثات مرتبة حسب آخر تحديث
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    return conversations


# جلب رسائل محادثة معيّنة
@router.get("/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    # التأكد أن المحادثة موجودة
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    # جلب الرسائل حسب ترتيب إنشائها
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return {
        "conversation_id": conversation_id,
        "title": conversation.title,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "original_text": message.original_text,
                "sanitized_text": message.sanitized_text,
                "response_text": message.response_text,
                "has_sensitive_data": message.has_sensitive_data,
                "sensitive_types": message.sensitive_types,
                "evidence_file": message.evidence_file,
                "request_id": message.request_id,
                "created_at": message.created_at,
            }
            for message in messages
        ]
    }


# حذف محادثة معيّنة
@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    # البحث عن المحادثة قبل حذفها
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    # حذف المحادثة من قاعدة البيانات
    db.delete(conversation)
    db.commit()

    return {
        "message": "Conversation deleted successfully."
    }