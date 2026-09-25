from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

import models
import security

# 1. Configuración de la conexión a la base de datos (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Creación de las tablas en la base de datos la primera vez que se ejecuta
models.Base.metadata.create_all(bind=engine)

# 3. Definición del middleware (CORS) para evitar warnings en el IDE (ej. PyCharm/WebStorm)
middleware_1 = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"], # Permite peticiones desde cualquier sitio (como nuestro frontend local)
        allow_credentials=True,
        allow_methods=["*"], # Permite todos los métodos (GET, POST, etc.)
        allow_headers=["*"], # Permite todos los headers
    )
]

# 4. Inicialización de la aplicación FastAPI con el middleware integrado
app = FastAPI(title="Auth Service API", middleware=middleware_1)


# 5. Dependencia para inyectar la sesión de la base de datos en las rutas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 6. Esquemas de validación de datos usando Pydantic
class PasswordResetRequest(BaseModel):
    email: EmailStr # Valida automáticamente que sea un formato de correo válido


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# 7. Endpoint 1: Solicitar la recuperación de contraseña
@app.post("/api/auth/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    # Buscamos si el usuario existe en la base de datos
    user = db.query(models.User).filter(models.User.email == request.email).first()

    if user:
        # Generamos el token seguro (crudo), su hash para la DB y su fecha de expiración
        raw_token, token_hash, expires_at = security.generate_reset_token()

        # Guardamos SOLO el hash en la base de datos
        db_token = models.ResetToken(
            token_hash=token_hash,
            user_email=user.email,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()

        # Simulamos el envío del correo imprimiendo el token crudo en la consola
        print(f"MOCK EMAIL: Tu token es -> {raw_token}")

    # Siempre retornamos el mismo mensaje para no revelar si un correo está registrado o no (Seguridad)
    return {"message": "Si el correo está registrado, recibirás un enlace de recuperación."}


# 8. Endpoint 2: Validar el token y establecer la nueva contraseña
@app.post("/api/auth/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    # Hasheamos el token recibido para poder buscarlo en la base de datos
    token_hash = security.hash_token(request.token)

    # Buscamos el token en la tabla
    db_token = db.query(models.ResetToken).filter(models.ResetToken.token_hash == token_hash).first()

    # Validación 1: ¿El token existe?
    if not db_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enlace inválido")

    # Validación 2: ¿El token ya fue usado antes?
    if db_token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El enlace ya fue utilizado")

    # Restauramos la zona horaria UTC a la fecha extraída de SQLite
    expires_at_aware = db_token.expires_at.replace(tzinfo=timezone.utc)

    # Validación 3: ¿El token expiró? (Validación de 1 minuto configurada en security.py)
    if datetime.now(timezone.utc) > expires_at_aware:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El enlace ha expirado")

    # Si pasa todas las validaciones, procedemos a actualizar la contraseña
    user = db.query(models.User).filter(models.User.email == db_token.user_email).first()
    if user:
        user.hashed_password = security.get_password_hash(request.new_password)

    # Marcamos el token como utilizado para invalidarlo permanentemente
    db_token.used = True
    db.commit()

    return {"message": "Contraseña actualizada exitosamente"}