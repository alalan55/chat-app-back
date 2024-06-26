from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from service.auth import AuthService
from service.messages import MessageService
from typing import Optional
from schemas.user_schema import UserRequestStatus, UpdateUser
from schemas.messages_schema import ConversationType

import models


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def health(self):
        return 'User service health'

    async def update_profile(self, id: int, info: UpdateUser, user: dict):

        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid and user.get('id') == id:

            updated_user = self.session.query(
                models.Users).filter(models.Users.id == id).first()
            updated_user.name = info.name
            updated_user.profile_pic = info.profile_pic
            updated_user.coverage_pic = info.coverage_pic
            updated_user.status = info.status
            updated_user.shared_id = info.shared_id

            self.session.add(updated_user)
            self.session.commit()

            return f'Usuário {info.name} atualizado com suecsso'

    async def get_user_info(self, id: int, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)
        if user_is_valid:
            user_info = self.session.query(models.Users).filter(
                models.Users.id == id).first()

            # pegar quantidade de amigos
            friends_quantity = len(self.get_friends_list(user))

            # pegar a quantidade de grupos
            conversations = await MessageService(self.session).get_chat_list(user)
            groups_quantity = len(list(filter(lambda group: group.get(
                'conversation_type') == ConversationType.GROUP.value, conversations)))

            # pegar a quantidade de mensagens enviadas
            messages_quantity = len(self.session.query(models.Messages).filter(
                models.Messages.from_user == user_info.shared_id).all())

            user_info.friends_quantity = friends_quantity
            user_info.messages_quantity = messages_quantity
            user_info.groups_quantity = groups_quantity

            return user_info

    def get_friends_list(self, user: dict):

        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:

            user_id = user.get('id')

            friends = self.session.query(models.Users).join(
                models.Friends, models.Users.shared_id == models.Friends.friend_id).filter(models.Friends.owner_id == user_id).all()

            return friends

    def get_friends_requests(self, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:

            # friends = self.session.query(models.FriendsRequests).filter(
            #     models.FriendsRequests.friend_id == user.get('id')).all()

            friends = self.session.query(models.Users, models.FriendsRequests).join(
                models.FriendsRequests, models.Users.shared_id == models.FriendsRequests.applicant_shared_id).filter(models.FriendsRequests.friend_id == user.get('id')).all()

            friends_info = []

            for user_info, request_info in friends:
                friend_dict = {
                    "user_id": user_info.id,
                    "user_name": user_info.name,
                    "user_email": user_info.email,
                    "user_profile_pic": user_info.profile_pic,
                    "user_shared_id": user_info.shared_id,
                    "friend_request_id": request_info.id,
                    "friend_applicant_id": request_info.applicant_id,
                    "friend_applicant_shared_id": request_info.applicant_shared_id,
                    "friend_friend_shared_id": request_info.friend_shared_id,
                    "friend_id": request_info.friend_id,
                    "friend_status": request_info.status
                }
                friends_info.append(friend_dict)

            return friends_info

    def delete_friendship(self, shared_id: str, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:
            user_id = user.get('id')

            current_user = self.session.query(models.Users).filter(
                models.Users.id == user_id).first()

            user_to_remove = self.session.query(models.Users).filter(
                models.Users.shared_id == shared_id).first()

            friend = self.session.query(models.Friends).filter(
                models.Friends.friend_id == shared_id).filter(models.Friends.owner_id == user_id).first()

            if friend is None:
                raise HTTPException(
                    status_code=404, detail='Esse usuário não está na sua lista de amigos')

            self.session.query(models.Friends).filter(
                models.Friends.friend_id == shared_id).filter(models.Friends.owner_id == user_id).delete()
            self.session.commit()

            # a linha abaixo remove também o usuário atual da lista do usuário que foi deletado
            self.session.query(models.Friends).filter(
                models.Friends.friend_id == current_user.shared_id).filter(models.Friends.owner_id == user_to_remove.id).delete()
            self.session.commit()

            return

    def change_friendship_status(self, status: str, shared_id: str, user_id: int):
        friendship_requested = self.session.query(models.FriendsRequests).filter(
            models.FriendsRequests.applicant_shared_id == shared_id).filter(models.FriendsRequests.friend_id == user_id).first()

        if friendship_requested:
            friendship_requested.status = status
            self.session.add(friendship_requested)
            self.session.commit()

        return

    def add_user_to_my_current_list(self, user_id: int, shared_id: str):
        friends_model = models.Friends()
        friends_model.owner_id = user_id
        friends_model.friend_id = shared_id

        self.session.add(friends_model)
        self.session.commit()

        return

    def add_friend(self, shared_id: str, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:

            current_user_id = user.get('id')

            user_to_add = self.session.query(models.Users).filter(
                models.Users.shared_id == shared_id).first()

            current_user = self.session.query(models.Users).filter(
                models.Users.id == current_user_id).first()

            if user_to_add is None:
                raise HTTPException(
                    status_code=404, detail='Usuário não encontrado na base de dados')

            already_has_requested = self.session.query(models.FriendsRequests).filter(
                models.FriendsRequests.friend_shared_id == shared_id).filter(models.FriendsRequests.applicant_id == current_user_id).first()

            if already_has_requested is None:
                friend_incoming_model = models.FriendsRequests()
                friend_incoming_model.applicant_shared_id = current_user.shared_id
                friend_incoming_model.applicant_id = user.get('id')
                friend_incoming_model.friend_id = user_to_add.id
                friend_incoming_model.friend_shared_id = shared_id
                friend_incoming_model.status = UserRequestStatus.PENDING.value

                self.session.add(friend_incoming_model)
                self.session.commit()

                return UserRequestStatus.OK.value

            return UserRequestStatus[already_has_requested.status.upper()].value

    async def friendship_management(self, user_to_add_id: str, user: dict, friendship_accept: bool):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:

            if friendship_accept:
                status = await self.handle_acepted_friend(user_to_add_id, user.get('id'))
                return status
            else:
                self.change_friendship_status(
                    'refused', user_to_add_id, user.get('id'))
                return 'refused'

    async def handle_acepted_friend(self, user_to_add_id: str, current_user_id: int):

        user_to_add = self.session.query(models.Users).filter(
            models.Users.shared_id == user_to_add_id).first()

        if user_to_add is None:
            raise HTTPException(
                status_code=404, detail='Usuário não encontrado na base de dados')

        current_user = self.session.query(models.Users).filter(
            models.Users.id == current_user_id).first()

        user_to_add_is_on_list = self.session.query(models.Friends).filter(
            models.Friends.friend_id == user_to_add.shared_id).filter(models.Friends.owner_id == current_user_id).first()

        if not user_to_add_is_on_list:
            self.add_user_to_my_current_list(current_user_id, user_to_add_id)

            self.change_friendship_status(
                'accepted', user_to_add_id, current_user_id)

            self.add_user_to_my_current_list(
                user_to_add.id, current_user.shared_id)

            return 'accepted'

        return 'invalid'


def custom_message(status: Optional[int] = 200, content: Optional[dict | list | str | int] = None, message: Optional[str] = None):
    return {
        'status': status,
        'message': message,
        'content': content
    }


# ao aceitar um asolicitação, os usuários tem que ser inseridos em ambas as listas
# ao apagar uma solicitação, os usuários tem que ser excluidos mutuamente
