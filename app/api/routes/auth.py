from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import RegisterRequest, LoginRequest, AuthResponse
from app.core.database import get_db, User
from app.core.security import hash_password, verify_password


# راوتر خاص بعمليات التسجيل والدخول
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# تسجيل مستخدم جديد
@router.post("/register", response_model=AuthResponse)
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    # التأكد أن اسم المستخدم غير مستخدم
    existing_username = db.query(User).filter(User.username == request.username).first()
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )

    # التأكد أن البريد غير مستخدم
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists."
        )

    # إنشاء المستخدم مع تشفير كلمة المرور
    new_user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password)
    )

    # حفظ المستخدم في قاعدة البيانات
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return AuthResponse(
        message="User registered successfully.",
        user=new_user
    )


# تسجيل الدخول
@router.post("/login", response_model=AuthResponse)
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    # البحث عن المستخدم باسم المستخدم
    user = db.query(User).filter(User.username == request.username).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    # التحقق من كلمة المرور
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    return AuthResponse(
        message="Login successful.",
        user=user
    )