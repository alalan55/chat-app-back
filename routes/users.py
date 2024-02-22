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
