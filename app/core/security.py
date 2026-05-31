from pwdlib import PasswordHash


# تجهيز أداة تشفير كلمات المرور
password_hasher = PasswordHash.recommended()


# تشفير كلمة المرور قبل حفظها
def hash_password(password: str) -> str:
    return password_hasher.hash(password)


# التحقق من كلمة المرور عند تسجيل الدخول
def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_hasher.verify(plain_password, password_hash)