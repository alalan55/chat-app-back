# nome, email, senha, foto de perfil, id, shared_id(automatico

from database import Base, engine
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    profile_pic = Column(String)
    shared_id = Column(Integer)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    friends = relationship('Friends', back_populates='friend_id')


class Friends(Base):
    __tablename__ = 'friends'

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))

    friend_id = relationship('Users', back_populates='friends')


Base.metadata.create_all(bind=engine)
