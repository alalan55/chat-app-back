
from fastapi import WebSocket
from typing import List


class NotificationService:
    def __init__(self):
        # self.websockets_list = websockets_list
        self.websockets_list: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.websockets_list.append(ws)
        return

    async def disconnect(self, ws: WebSocket):
        ws.close()
        self.websockets_list.remove(ws)

    async def get_websockets_list(self):
        return self.websockets_list

    # async def send_notification
