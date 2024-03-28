from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import timedelta, datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional
import bcrypt
import models
import string
import random

router = APIRouter()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGOTITHM = 'HS256'


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateUser(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


@router.post('/')
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    user_model = models.Users()
    user_model.name = user.name
    user_model.email = user.email
    user_model.shared_id = create_random_shared_id(10)
    user_model.hashed_password = password_hash(user.password)

    db.add(user_model)
    db.commit()

    return user_model


@router.post('/login')
async def login(user: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(user.email, user.password, db=db)

    if not user:
        raise HTTPException(
            status_code=401, detail='Usuário ou senha incorretos')

    token_expires = timedelta(minutes=60)
    token = create_access_token(
        user.email, user.id, expires_delta=token_expires)

    user.hashed_password = None
    return successful_response(200, token, user)


def create_access_token(email: str, id: int, expires_delta: Optional[timedelta] = None):
    encode = {'sub': email, 'id': id}

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    encode.update({'exp': expire})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGOTITHM)


def password_hash(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password=password_bytes, salt=salt)


def verify_password(password, hadshed):
    password_byte = password.encode('utf-8')
    return bcrypt.checkpw(password=password_byte, hashed_password=hadshed)


def authenticate_user(email: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.email == email).first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGOTITHM)
        email: str = payload.get('sub')
        id: int = payload.get('id')

        if email is None or id is None:
            raise HTTPException(
                status_code=404, detail='Usuário não encontrado')
        return {'email': email, 'id': id}
    except JWTError:
        raise HTTPException(
            status_code=404, detail='Não foi possível validar as credenciais')


def create_random_shared_id(n: int):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


def successful_response(status_code: int, token: Optional[str] = None, content: Optional[dict] = None):
    return {
        "status": status_code,
        "message": "Sucesso!",
        "content": content,
        "token": token
    }


def get_user_exception():
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Não foi possível validar as credenciais", headers={"WWW-Authenticate": "Bearer"})
    return credential_exception