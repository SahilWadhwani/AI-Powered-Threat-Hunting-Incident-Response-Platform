from passlib.context import CryptContext

# Argon2id with sensible defaults; passlib picks good params for dev.
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)