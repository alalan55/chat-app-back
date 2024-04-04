from fastapi import APIRouter
from database import SessionLocal
from service.messages import MessageService


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get('/messages-test')
async def health_messages():
    message = MessageService().start_session
    print('ROUTER', message)

    return message
