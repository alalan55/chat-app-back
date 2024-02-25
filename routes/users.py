from fastapi import APIRouter, Depends, HTTPException, status
from database import SessionLocal
from sqlalchemy.orm import Session
from routes.auth import get_current_user, get_user_exception
from service.user import UserService
from typing import Optional
from schemas.user_schema import FriendRequestIncoming
import models

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post('/manage-friendship')
async def accept_or_refuse_friendship(friend_request: FriendRequestIncoming, shared_id: str, friendship_accept: bool, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    if friendship_accept:
        user_to_add = db.query(models.Users).filter(
            models.Users.shared_id == shared_id).first()

        if user_to_add is None:
            raise HTTPException(
                status_code=404, detail='Usuário não encontrado na base de dados')

        user_to_add_is_on_list = db.query(models.Friends).filter(
            models.Friends.id == user_to_add.id).first()

        if not user_to_add_is_on_list:
            UserService(db).add_user_to_my_current_list(
                user.get('id'), shared_id)

            UserService(db).change_friendship_status(
                'accept', shared_id, user.get('id'))

            return custom_message(200, None, f'Usuário {friend_request.applicant_shared_id} Adicionado na sua lista de amizades!')
        else:
            return 'Usuário já está na sua lista de amizades'
    else:
        UserService(db).change_friendship_status(
            'refused', shared_id, user.get('id'))
        return f'Usuário {friend_request} recusado!'


@router.post('/add-friend')
async def add_friend(shared_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    response_info = UserService(db).add_friend(shared_id, user)

    if response_info == 'ok':
        return custom_message(status.HTTP_200_OK, None, 'Pedido de amizado enviado com sucesso :)')

    if response_info == 'pending':
        return custom_message(status.HTTP_204_NO_CONTENT, None, 'Aguarde o usuário aceitar a sua solicitação')

    if response_info == 'accepted':
        return custom_message(status.HTTP_204_NO_CONTENT, None, 'Usuário já está na sua lista de amigos :)')

    if response_info == 'refused':
        return custom_message(status.HTTP_204_NO_CONTENT, None, 'Usuário recusou sua solicitação')


@router.get('/friends')
async def get_friends_list(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    friends = UserService(db).get_friends_list(user)
    return custom_message(status.HTTP_200_OK, friends, '')


@router.get('/friends-request')
async def get_friends_requests(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    friends = UserService(db).get_friends_requests(user)
    return custom_message(status.HTTP_200_OK, friends, '')


@router.delete('/friends/{shared_id}')
async def remove_friend(shared_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    UserService(db).delete_friendship(shared_id, user)
    return custom_message(status.HTTP_200_OK, None, 'Usuário removido da sua lista de amizades :)')


def custom_message(status: Optional[int] = 200, content: Optional[dict | list | str | int] = None, message: Optional[str] = None):
    return {
        'status': status,
        'message': message,
        'content': content
    }
