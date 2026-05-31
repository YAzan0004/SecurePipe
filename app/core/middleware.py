import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.logging import logger


# Middleware لإضافة رقم تتبع لكل طلب
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # إنشاء رقم فريد للطلب الحالي
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # حساب وقت بداية الطلب
        start_time = time.time()

        # تسجيل بداية الطلب في السجل
        logger.info(
            f"REQUEST START | request_id={request_id} | method={request.method} | path={request.url.path}"
        )

        # تمرير الطلب لباقي النظام
        response = await call_next(request)

        # حساب مدة تنفيذ الطلب
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # إضافة رقم التتبع في هيدر الاستجابة
        response.headers["X-Request-ID"] = request_id

        # تسجيل نهاية الطلب في السجل
        logger.info(
            f"REQUEST END | request_id={request_id} | status_code={response.status_code} | duration_ms={duration_ms}"
        )

        return response