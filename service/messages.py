from sqlalchemy.orm import Session
from typing import Optional


class MessageService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session

    async def start_session(self):
        message: str = 'messages services work'
        print('SERVICE', message)
        return message
