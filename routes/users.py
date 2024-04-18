from fastapi import APIRouter, Depends,  status
from database import SessionLocal
from sqlalchemy.orm import Session
from service.user import UserService
from service.auth import AuthService
from typing import Optional
from schemas.user_schema import UserListResponse
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('/manage-friendship')
async def accept_or_refuse_friendship(user_to_add_id: str, friendship_accept: bool, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    current_status = UserService(db).friendship_management(
        user_to_add_id, user, friendship_accept)

    if current_status == 'accepted':
        return custom_message(status.HTTP_200_OK, None, f'Usuário {user_to_add_id} adicionado na sua lista de amizades!')

    if current_status == 'invalid':
        return custom_message(status.HTTP_204_NO_CONTENT, None, 'Usuário já está na sua lista de amizades!')

    if current_status == 'refused':
        return custom_message(status.HTTP_204_NO_CONTENT, None, f'Usuário {user_to_add_id} recusado!')


@router.get('/add-friend')
async def add_friend(user_to_add_id: str, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    response_info = UserService(db).add_friend(user_to_add_id, user)

    if response_info == 'ok':
        return custom_message(status.HTTP_200_OK, None, 'Pedido de amizado enviado com sucesso :)')

    if response_info == 'pending':
        return custom_message(status.HTTP_204_NO_CONTENT, None, 'Aguarde o usuário aceitar a sua solicitação')

    if response_info == 'accepted':
        return custom_message(status.HTTP_204_NO_CONTENT, None, 'Usuário já está na sua lista de amigos :)')

    if response_info == 'refused':
        return custom_message(status.HTTP_204_NO_CONTENT, None, 'Usuário recusou sua solicitação')


@router.get('/friends', response_model=UserListResponse)
async def get_friends_list(db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    friends = UserService(db).get_friends_list(user)
    return custom_message(status.HTTP_200_OK, friends, '')


@router.get('/friends-request', response_model=UserListResponse)
async def get_friends_requests(db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    friends = UserService(db).get_friends_requests(user)
    return custom_message(status.HTTP_200_OK, friends, '')


@router.delete('/friends/{shared_id}')
async def remove_friend(shared_id: str, db: Session = Depends(get_db), user: dict = Depends(AuthService().get_current_user)):
    UserService(db).delete_friendship(shared_id, user)
    return custom_message(status.HTTP_200_OK, None, 'Usuário removido da sua lista de amizades :)')


def custom_message(status: Optional[int] = 200, content: Optional[dict | list | str | int] = None, message: Optional[str] = None):
    return {
        'status': status,
        'message': message,
        'content': content
    }
