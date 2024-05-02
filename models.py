# nome, email, senha, foto de perfil, id, shared_id(automatico

from database import Base, engine
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from typing import List


association_table_friend_group_member = Table('association_table_friend_group_member', Base.metadata,
                                              Column('group_member_id', ForeignKey(
                                                  'groupMembers.id')),
                                              Column('user_id', ForeignKey('users.id')))


class Users(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    profile_pic = Column(String)
    shared_id = Column(Integer)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    group_memberships = relationship("GroupMembers", back_populates="user")


class Friends(Base):
    __tablename__ = 'friends'

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    # friend_id = Column(String, nullable=True)
    friend_id = Column(String, ForeignKey('users.shared_id'))
    user = relationship('Users', foreign_keys=[owner_id],  backref='user_info')
    friend = relationship('Users', foreign_keys=[
                          friend_id], backref='friend_info')
    # friend_id = relationship('Users', back_populates='friends')


class FriendsRequests (Base):
    __tablename__ = 'friendsRequests'

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey('users.id'))
    applicant_shared_id = Column(String)
    friend_shared_id = Column(String, default='pending')
    friend_id = Column(Integer)
    status = Column(String)


class Conversations(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    converation_name = Column(String)
    conversation_type = Column(Integer)
    messages = relationship('Messages', back_populates='messageConversation')
    groupMember = relationship('GroupMembers', back_populates='conversation')


class GroupMembers(Base):
    __tablename__ = 'groupMembers'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_datetime = Column(String)
    left_datetime = Column(String)
    user = relationship("Users", back_populates="group_memberships")
    conversation = relationship('Conversations', back_populates='groupMember')

    user_member_id: Mapped[List[Users]] = relationship(
        secondary=association_table_friend_group_member)


class Messages(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    from_user_name = Column(String)
    from_user = Column(String)
    to_user = Column(String)
    message_text = Column(String)
    sent_datetime = Column(String)
    messageConversation = relationship(
        'Conversations', back_populates='messages')


Base.metadata.create_all(bind=engine)
