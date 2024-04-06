from fastapi import APIRouter, Depends
from database import SessionLocal
from sqlalchemy.orm import Session
from service.messages import MessageService
from service.auth import AuthService
from schemas.messages_schema import CreateConversation, SendMessage
from response.messages import successful_response


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
    return f'{conversation}'


@router.get('/chat-list')
async def get_chat_list(db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    chat_list = await MessageService(db).get_chat_list(user)
    return successful_response(200, None, chat_list, '')


@router.post('/chating')
async def send_message(info: SendMessage, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    response = await MessageService(db).create_message(info, user)
    return successful_response(200, None, response, '')
