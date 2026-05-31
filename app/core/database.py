from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


# رابط قاعدة البيانات المحلية SQLite
DATABASE_URL = "sqlite:///./securepipe.db"

# إنشاء محرك الاتصال بقاعدة البيانات
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# تجهيز جلسات الاتصال بقاعدة البيانات
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# الأساس الي تبنى عليه جداول قاعدة البيانات
Base = declarative_base()


# جدول المستخدمين
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ربط المستخدم بمحادثاته
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# جدول المحادثات
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # ربط المحادثة بالمستخدم
    user = relationship("User", back_populates="conversations")

    # ربط المحادثة بالرسائل التابعة لها
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


# جدول الرسائل
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)

    role = Column(String(50), nullable=False)  # user / assistant

    # تخزين النص الأصلي والنص بعد الفلترة ورد الذكاء الاصطناعي
    original_text = Column(Text, nullable=True)
    sanitized_text = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)

    # معلومات عن وجود بيانات حساسة وأنواعها
    has_sensitive_data = Column(Boolean, default=False)
    sensitive_types = Column(Text, nullable=True)

    # معلومات التتبع وملف الإثبات
    evidence_file = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ربط الرسالة بالمحادثة
    conversation = relationship("Conversation", back_populates="messages")


# إنشاء الجداول إذا لم تكن موجودة
def create_database_tables():
    Base.metadata.create_all(bind=engine)


# فتح جلسة قاعدة بيانات ثم إغلاقها بعد الاستخدام
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()