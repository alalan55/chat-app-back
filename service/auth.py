from sqlalchemy.orm import Session
import string
import random
import bcrypt
import models
from schemas.auth_schema import CreateUser, UserLogin
from fastapi import HTTPException
from datetime import timedelta, datetime
from typing import Optional
from jose import jwt, JWTError


SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGOTITHM = 'HS256'


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def user_is_validated(self, user: dict):

        if user is None:
            return False
        else:
            return True

    def create_user(self, user: CreateUser):
        user_model = models.Users()
        user_model.name = user.name
        user_model.email = user.email
        user_model.shared_id = create_random_shared_id(10)
        user_model.hashed_password = password_hash(user.password)

        self.session.add(user_model)
        self.session.commit()

        return user_model

    def login(self, user: UserLogin):
        user = self.authenticate_user(user.email, user.password)

        if not user:
            raise HTTPException(
                status_code=401, detail='Usuário ou senha incorretos')

        token_expires = timedelta(minutes=60)
        token = self.create_access_token(
            user.email, user.id, expires_delta=token_expires)

        user.hashed_password = None

        return token, user

    def authenticate_user(self, email: str, password: str):
        user = self.session.query(models.Users).filter(
            models.Users.email == email).first()

        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user

    def create_access_token(self, email: str, id: str, expires_delta: Optional[timedelta] = None):
        encode = {'sub': email, 'id': id}

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        encode.update({'exp': expire})

        return jwt.encode(encode, SECRET_KEY, algorithm=ALGOTITHM)


def create_random_shared_id(n: int):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


def password_hash(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password=password_bytes, salt=salt)


def verify_password(password, hadshed):
    password_byte = password.encode('utf-8')
    return bcrypt.checkpw(password=password_byte, hashed_password=hadshed)
