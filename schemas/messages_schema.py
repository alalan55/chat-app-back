from pydantic import BaseModel
from schemas.user_schema import UserToBeReturnedToFriends
from typing import Dict
import enum


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


class UserGroupRole(enum.Enum):
    ADMIN = 0
    NORMAL = 1


class TestModel(BaseModel):
    id: int
    conversation_name: str
    conversation_type: int
    created_by: int
    participants: list[UserToBeReturnedToFriends]
    # creator: Dict[str, UserToBeReturnedToFriends]
    # creator: UserToBeReturnedToFriends
    creator:  str


class GroupInfoResponse(BaseModel):
    status: int
    message: str
    content: TestModel
