from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

import models
import security

# Configuración de base de datos SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Esto crea el archivo app.db y las tablas la primera vez que se ejecuta
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service API")


# Dependencia para interactuar con la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Esquemas de entrada
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@app.post("/api/auth/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()

    if user:
        raw_token, token_hash, expires_at = security.generate_reset_token()

        db_token = models.ResetToken(
            token_hash=token_hash,
            user_email=user.email,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()

        # Imprime el token en la consola para que puedas copiarlo y probar
        print(f"MOCK EMAIL: Tu token es -> {raw_token}")

    return {"message": "Si el correo está registrado, recibirás un enlace de recuperación."}


@app.post("/api/auth/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = security.hash_token(request.token)

    db_token = db.query(models.ResetToken).filter(models.ResetToken.token_hash == token_hash).first()

    if not db_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enlace inválido")

    if db_token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El enlace ya fue utilizado")

    if datetime.now(timezone.utc) > db_token.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El enlace ha expirado")

    user = db.query(models.User).filter(models.User.email == db_token.user_email).first()
    if user:
        user.hashed_password = security.get_password_hash(request.new_password)

    db_token.used = True
    db.commit()

    return {"message": "Contraseña actualizada exitosamente"}