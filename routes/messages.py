from fastapi import APIRouter, Depends
from database import SessionLocal
from sqlalchemy.orm import Session
from service.messages import MessageService
from service.auth import AuthService
from schemas.messages_schema import CreateConversation


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('/messages-test')
async def health_messages():
    message = await MessageService().start_session()
    return message


@router.post('/create-conversation')
async def create_conversation(conversation: CreateConversation, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    conversation = await MessageService(db).create_conversation(conversation, user)
    return f'{conversation}, hello, aqui foi feito'
