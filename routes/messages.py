from fastapi import APIRouter, Depends,  WebSocket, WebSocketDisconnect, Query, FastAPI
from fastapi.concurrency import run_in_threadpool
from starlette.websockets import WebSocketState
from database import SessionLocal
from typing import Optional
from sqlalchemy.orm import Session
from service.messages import MessageService, event_queue
from service.notification import NotificationService
from service.auth import AuthService
from schemas.messages_schema import CreateConversation, SendMessage, GroupInfoResponse
from response.messages import successful_response
from typing import List

import asyncio
from contextlib import asynccontextmanager
from queue import Empty


router = APIRouter(prefix='/message', tags=['Messages'])

notification_service = NotificationService()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_dependencies(db: Session = Depends(get_db)):
    return db


message_manager = MessageService(get_database_dependencies())
connections = MessageService(get_database_dependencies()).active_connections


@router.get('/health-message')
async def health_messages():
    message = await MessageService().start_session()
    return message


@router.get('/chat-list')
async def get_chat_list(db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    chat_list = await MessageService(db).get_chat_list(user)
    return successful_response(200, None, chat_list, '')


@router.post('/create-conversation')
async def create_conversation(conversation: CreateConversation, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    conversation = await MessageService(db).create_conversation(conversation, user)
    # print(list(event_queue.queue), 'lista no create conversation')
    return f'{conversation}'


@router.post('/chating')
async def send_message(info: SendMessage, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    response = await MessageService(db).create_message(info, user)
    return successful_response(200, None, response, '')


@router.get('/get-chat-info/{chat_id}', response_model=GroupInfoResponse)
async def get_chat_information(chat_id: int, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    chat_info = await MessageService(db).get_current_chat_info(chat_id, user)
    return custom_message(200, chat_info, 'Sucesso!')


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


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):

    await notification_service.connect(websocket)

    try:
        while True:
            try:
                # Tente obter um evento da fila, mas não bloqueie
                event = event_queue.get_self().get_nowait()
                ws_list = await notification_service.get_websockets_list()

                for ws in ws_list:
                    await ws.send_json(event)

            except Empty:
                if websocket.client_state != WebSocketState.CONNECTED:
                    break
                await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    finally:
        await notification_service.disconnect(websocket)


async def event_notifier(stop_event: asyncio.Event):
    while True and not stop_event.is_set():
        try:
            event = event_queue.get_self().get_nowait()
            disconnected_websockets = []

            # Notifica todos os WebSockets conectados sobre o evento
            ws_list = await notification_service.get_websockets_list()

            for ws in ws_list:
                if ws.client_state == WebSocketState.CONNECTED:
                    try:
                        await run_in_threadpool(ws.send_json(event)) 
                    except WebSocketDisconnect:
                        disconnected_websockets.append(ws)
                else:
                    disconnected_websockets.append(ws)

            for ws in disconnected_websockets:
                await notification_service.disconnect(ws)
        # except Empty:
        #     await asyncio.sleep(1)
        except asyncio.QueueEmpty:
            pass
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    event_notifier_task = asyncio.create_task(event_notifier(stop_event))
    try:
        yield
    finally:
        # event_notifier_task.cancel()
        stop_event.set()
        await event_notifier_task
        ws_list = await notification_service.get_websockets_list()
        for ws in ws_list:
            await ws.close()


def custom_message(status: Optional[int] = 200, content: Optional[dict | list | str | int] = None, message: Optional[str] = None):
    return {
        'status': status,
        'message': message,
        'content': content
    }


# @router.websocket('/ws')
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     websockets.append(websocket)
#     # print('pre lista de ws', websockets)
#     try:
#         while True:
#             if websocket.client_state != WebSocketState.CONNECTED:
#                 break
#             try:
#                 # Tente obter um evento da fila, mas não bloqueie
#                 event = event_queue.get_nowait()
#                 await websocket.send_json({'conversation_created': 'test', 'notification_type': 1})
#             except asyncio.QueueEmpty:
#                 await asyncio.sleep(0.1)
#                 continue

#             await websocket.send_json({'conversation_created': event, 'notification_type': 1})

#     except WebSocketDisconnect:

#         pass
#     finally:
#         websockets.remove(websocket)


# async def event_notifier():
#     while True:
#         try:
#             event = event_queue.get_nowait()
#             print('entrei aqui')
#             # Notifica todos os WebSockets conectados sobre o evento
#             for ws in websockets:
#                 if ws.client_state == WebSocketState.CONNECTED:
#                     await run_in_threadpool(ws.send_text, f"Novo evento: {event}")
#         except asyncio.QueueEmpty:
#             await asyncio.sleep(0.1)
