from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from typing import Optional
from service.auth import AuthService
from schemas.auth_schema import CreateUser, UserLogin

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post('/')
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    user_model = AuthService(db).create_user(user)
    # Verificafr motivo de não estar retornando o usuário criado
    return user_model


@router.post('/login')
async def login(user: UserLogin, db: Session = Depends(get_db)):
    token, user = AuthService(db).login(user)
    return successful_response(200, token, user)


def successful_response(status_code: int, token: Optional[str] = None, content: Optional[dict] = None):
    return {
        "status": status_code,
        "message": "Sucesso!",
        "content": content,
        "token": token
    }


# def get_user_exception():
#     credential_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED, detail="Não foi possível validar as credenciais", headers={"WWW-Authenticate": "Bearer"})
#     return credential_exception
