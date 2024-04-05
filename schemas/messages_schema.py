from pydantic import BaseModel


class CreateConversation(BaseModel):
    friends_list: list[int]
    name: str
