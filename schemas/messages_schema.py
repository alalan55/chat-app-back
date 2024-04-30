from pydantic import BaseModel


class CreateConversation(BaseModel):
    friends_list: list[int]
    conversation_type: int
    name: str


class SendMessage(BaseModel):
    conversation_id: int
    from_user: str
    to_user: str
    message_text: str
    sent_datetime: str