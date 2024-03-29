import enum
from pydantic import BaseModel
from typing import Optional, List


class FriendRequestIncoming(BaseModel):
    # applicant_id: int
    applicant_shared_id: str
    friend_shared_id: str


class UserRequestStatus(enum.Enum):
    OK = 'ok'
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REFUSED = 'refused'


class UserToBeReturnedToFriends(BaseModel):
    id: int
    name: str
    email: str
    profile_pic: Optional[str] = None
    shared_id: str
    is_active: bool


class UserListResponse(BaseModel):
    status: int
    message: str
    content: List[UserToBeReturnedToFriends]

# friend_shared_id deve virar my_shared_id
# friend_id deve virar my_id
# Ao apagar um amigo, devo mudar o status dele para excluded (logo ele pode receber solicitações de amizade novamente)
# Ao adicioanr um amigo, a lista de amigos deve ser atualizada para o socilitador e para quem aceita
