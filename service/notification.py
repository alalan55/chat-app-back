
from fastapi import WebSocket
from typing import List


class NotificationService:
    def __init__(self, websockets_list: List[WebSocket]):
        self.websockets_list = websockets_list

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.websockets_list.append(ws)
        return

    # async def send_notification