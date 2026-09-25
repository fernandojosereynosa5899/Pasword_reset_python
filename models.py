# model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

base = declarative_base()

class User(base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class ResetToken(base):
    __tablename__ = 'reset_tokens'
    token_hash = Column(String, primary_key=True, index=True)
    user_email = Column(String, ForeignKey=('users.email'), nullable=False)
    expires_date = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean,  default=False)