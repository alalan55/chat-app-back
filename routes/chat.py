import anyio
from starlette.concurrency import run_until_first_complete
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from broadcaster import Broadcast
import uuid
import json


router = APIRouter()

broadcast = Broadcast('memory://chat.db')


class ConenctionManager():
    def __init__(self) -> None:
        # self.active_connections: list[WebSocket] = []
        self.active_connections: dict = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        id = str(uuid.uuid4())
        self.active_connections[id] = ws

        await self.send_personal_message(json.dumps({"type": "connect", "id": id}), ws=ws)

    async def disconnect(self, ws: WebSocket):
        # self.active_connections.remove(ws)
        id = self.find_connection(ws)
        del self.active_connections[id]
        return id

    async def find_connection(self, ws: WebSocket):
        val_list = list(self.active_connections.values())
        key_list = list(self.active_connections.keys())
        id = val_list.index(ws)
        return key_list[id]

    async def send_personal_message(self, message: str, ws: WebSocket, ):
        await ws.send_text(message)

    async def broadcast_message(self, message: str):
        # for conn in self.active_connections:
        #     await conn.send_text(message)
        for conn in self.active_connections.values():
            await conn.send_text(message)


manager = ConenctionManager()


@router.websocket('/ws/{cliend_id}')
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
