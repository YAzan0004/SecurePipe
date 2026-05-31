from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, process, auth, conversations, admin
from app.core.middleware import RequestIDMiddleware
from app.core.database import create_database_tables


# إنشاء تطبيق FastAPI وتعريف معلومات المشروع
app = FastAPI(
    title="SecurePipe API",
    description="Privacy-aware AI gateway project",
    version="1.0.0"
)

# إضافة Middleware لتوليد رقم تتبع لكل طلب
app.add_middleware(RequestIDMiddleware)

# إنشاء جداول قاعدة البيانات عند تشغيل النظام
create_database_tables()

# ربط مسارات الـ API الرئيسية
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(process.router)
app.include_router(admin.router)

# تشغيل واجهة الويب من مجلد app/web
app.mount("/", StaticFiles(directory="app/web", html=True), name="web")