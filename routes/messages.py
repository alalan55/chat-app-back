from fastapi import APIRouter, Depends,  WebSocket, WebSocketDisconnect, Query
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


def get_database_dependencies(db: Session = Depends(get_db)):
    return db

message_manager = MessageService(get_database_dependencies())


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


@router.websocket('/connect-conversation/{conversation_id}')
async def chat(ws: WebSocket, conversation_id: int, token: str = Query(...), db: Session = Depends(get_db),):

    # continuar daqui, pois não é possivel fazer a validação de usuário em rotas ws por hora...
    # https://github.com/tiangolo/fastapi/issues/2587
    # https://indominusbyte.github.io/fastapi-jwt-auth/advanced-usage/websocket/
    # talvez mandar o token na rota e fazer uam validação interna?

    await message_manager.connect(ws, conversation_id)

    # pegar mensagens da conversation e enviar para o cliente
    messages = await MessageService(db).get_messages_of(token, conversation_id)

    for message in messages:
        await message_manager.send_personal_message(message, ws=ws)

    try:
        while True:
            data = await ws.receive_json()

            if "type" in data and data["type"] == "close":
                message_manager.disconnect(ws, conversation_id)
            else:
                # adicionar mensagem no banco de dados
                await MessageService(db).create_message_ws(data, token)

                # enviar mensagem para usuário
                await message_manager.broadcast_message_ws(data, conversation_id)

           # await message_manager.send_personal_message(f"You wrote: {data}", ws)

    except WebSocketDisconnect:
        message_manager.disconnect(ws, conversation_id)
        # await message_manager.broadcast_message(f'Cliente #{conversation_id} deixou o chat')
