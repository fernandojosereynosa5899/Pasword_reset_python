from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class ResetToken(Base):
    __tablename__ = 'reset_tokens'
    token_hash = Column(String, primary_key=True, index=True)
    # Corregido: ForeignKey se pasa como un argumento posicional, no como llave-valor
    user_email = Column(String, ForeignKey('users.email'), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)