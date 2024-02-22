from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session
from routes.auth import get_current_user, get_user_exception
import models

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post('/add-friend')
async def add_friend(shared_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):

    if user is None:
        raise get_user_exception()

    user_to_add = db.query(models.Users).filter(
        models.Users.shared_id == shared_id).first()

    if user_to_add is None:
        raise HTTPException(
            status_code=404, detail='Usuário não encontrado na base de dados')

    friends_model = models.Friends()
    friends_model.owner_id = user.get('id')
    friends_model.friend_id = shared_id

    db.add(friends_model)
    db.commit()

    return 'Usuário adicionado com sucesso'


@router.get('/friends')
async def get_friends_list(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    friends = db.query(models.Friends).filter(
        models.Friends.owner_id == user.get('id')).all()

    return friends


@router.delete('/friends/{shared_id}')
async def remove_friend(shared_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    friend = db.query(models.Friends).filter(
        models.Friends.friend_id == shared_id).first()

    if friend is None:
        raise HTTPException(
            status_code=404, detail='Esse usuário não está na sua lista de amigos')

    db.query(models.Friends).filter(
        models.Friends.friend_id == shared_id).delete()
    db.commit()

    return 'Usuário removido da sua lista de amizades :)'


# necessário criar uma tabela de amigos pendentes. Esta tabela vai ter o id do requerente, id do amigo desejado, status (pending, accepted, refused)
# ao adicionar um amigo, vai ser adicionado nessa tabela de amizades pendentes
# vai ter um listagem de todas as amizades pendentes
# o usuário vai poder aceitar ou recusar a amizade
# se a amizade for acecita, então ele é adicionado na lista de amigos e o status é alterado, se não, não é adicionado e o status também é alterado