# 1 Usuario deve se conectar
# 1.2 nome, email, senha, foto de perfil, id, shared_id(automatico
# 2 Usuário pode adicionar usuários na sua lista de amigos atraves do shared_id
# 3 Usuário pode mandar mensavem individual para esse shared_id
# 4 Usuário pode criar grupo e adicionar amigos nele

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from routes import auth
from database import engine, SessionLocal
import models


app = FastAPI()

app.include_router(auth.router)


class ConenctionManager():
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    async def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def send_personal_message(self, message: str, ws: WebSocket, ):
        await ws.send_text(message)

    async def broadcast_message(self, message: str):
        for conn in self.active_connections:
            await conn.send_text(message)


manager = ConenctionManager()


@app.get('/')
async def health():
    return 'Conectado'


@app.websocket('/ws/{cliend_id}')
async def chat(ws: WebSocket, cliend_id: int):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.broadcast_message(f'Cliente #{cliend_id} falou: {data}')
           # await manager.send_personal_message(f"You wrote: {data}", ws)
    except WebSocketDisconnect:
        manager.disconnect(ws)
        await manager.broadcast_message(f'Cliente #{cliend_id} deixou o chat')
