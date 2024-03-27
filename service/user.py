from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from service.auth import AuthService
from typing import Optional
from schemas.user_schema import UserRequestStatus

import models


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get_friends_list(self, user: dict):

        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:

            user_id = user.get('id')

            friends = self.session.query(models.Users).join(
                models.Friends, models.Users.shared_id == models.Friends.friend_id).filter(models.Friends.owner_id == user_id).all()

            # friends = self.session.query(models.Friends).filter(
            #     models.Friends.owner_id == user.get('id')).all()

            return friends

    def get_friends_requests(self, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:
            friends = self.session.query(models.FriendsRequests).filter(
                models.FriendsRequests.friend_id == user.get('id')).all()

            return friends

    def delete_friendship(self, shared_id: str, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:
            current_user = self.session.query(models.Users).filter(
                models.Users.id == user.get(id)).first()

            friend = self.session.query(models.Friends).filter(
                models.Friends.friend_id == shared_id).first()

            if friend is None:
                raise HTTPException(
                    status_code=404, detail='Esse usuário não está na sua lista de amigos')

            self.session.query(models.Friends).filter(
                models.Friends.friend_id == shared_id).delete()

            # a linha abaixo remove também o usuário atual da lista do usuário que foi deletado
            self.session.query(models.Friends).filter(
                models.Friends.friend_id == current_user.shared_id).delete()

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

    def friendship_management(self, user_to_add_id: str, user: dict, friendship_accept: bool):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:
            user_id = user.get('id')

            if friendship_accept:
                user_to_add = self.session.query(models.Users).filter(
                    models.Users.shared_id == user_to_add_id).first()

                if user_to_add is None:
                    raise HTTPException(
                        status_code=404, detail='Usuário não encontrado na base de dados')

                user_to_add_is_on_list = self.session.query(models.Friends).filter(
                    models.Friends.friend_id == user_to_add.shared_id).first()

                current_user = self.session.query(models.Users).filter(
                    models.Users.id == user_id).first()

                if not user_to_add_is_on_list:
                    self.add_user_to_my_current_list(user_id, user_to_add_id)

                    self.change_friendship_status(
                        'accepted', user_to_add_id, user_id)

                    # adicionar o usuário user_id na lista do user_to_add_id
                    self.add_user_to_my_current_list(
                        user_to_add.id, current_user.shared_id)

                    return 'accepted'
                else:
                    return 'invalid'
            else:
                self.change_friendship_status(
                    'refused', user_to_add_id, user_id)
                return 'refused'


def custom_message(status: Optional[int] = 200, content: Optional[dict | list | str | int] = None, message: Optional[str] = None):
    return {
        'status': status,
        'message': message,
        'content': content
    }


# ao aceitar um asolicitação, os usuários tem que ser inseridos em ambas as listas
# ao apagar uma solicitação, os usuários tem que ser excluidos mutuamente
