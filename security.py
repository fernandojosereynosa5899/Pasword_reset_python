# security.py
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from warnings import deprecated

from passlib.context import CryptContext


# Configuracion para encriptar la contraseña
pwd_contetx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_contetx.hash(password)


def generate_reset_token():
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=3)
    return raw_token, token_hash, expires_at


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


