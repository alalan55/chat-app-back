from fastapi import APIRouter, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
import bcrypt
import models

router = APIRouter()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class CreateUser(BaseModel):
    name: str
    email: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get('/auth')
async def auth():
    return 'Usuário autenticado'


@router.post('/')
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    user_model = models.Users()
    user_model.name = user.name
    user_model.email = user.email
    user_model.hashed_password = password_hash(user.password)

    db.add(user_model)
    db.commit()

    return user_model


def password_hash(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password=password_bytes, salt=salt)
