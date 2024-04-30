from sqlalchemy.orm import Session
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from service.auth import AuthService
from schemas.messages_schema import CreateConversation, SendMessage
import models
import uuid
import json


class MessageService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self.active_connections: dict[str, set[WebSocket]] = {}
        # informações das salas
        # print(self.active_connections, 'NO init do método aqui')

    async def connect(self, ws: WebSocket, room_id: int):
        await ws.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()

        self.active_connections[room_id].add(ws)

        # print(self.active_connections[room_id], 'conexão criada em')

    async def disconnect(self, ws: WebSocket, room_id: int):
        # self.active_connections.remove(ws)
        # id = self.find_connection(ws)
        # del self.active_connections[id]
        # return id
        self.active_connections[room_id].remove(ws)

    async def find_connection(self, ws: WebSocket):
        val_list = list(self.active_connections.values())
        key_list = list(self.active_connections.keys())
        id = val_list.index(ws)
        return key_list[id]

    async def send_personal_message(self, message: SendMessage, ws: WebSocket, ):
        # await ws.send_text(message)
        json_message = jsonable_encoder(message)
        await ws.send_json(json_message)

    async def broadcast_message(self, message: str):
        # for conn in self.active_connections:
        #     await conn.send_text(message)
        for conn in self.active_connections.values():
            await conn.send_text(message)

    async def broadcast_message_ws(self, message: SendMessage, room_id: int):
        # print(self.active_connections)
        for conn in self.active_connections[room_id]:
            await self.send_personal_message(message, conn)

    async def get_messages_of(self, token: str, room_id: int):

        user = AuthService(self.session).get_current_user(token=token)
        user_is_valid = AuthService(self.session).user_is_validated(user)

        print(room_id, 'ROOM ID')

        if user_is_valid:
            messages = self.session.query(models.Messages).filter(
                models.Messages.conversation_id == room_id).all()

            return messages

    # fim de informações das salas

    async def start_session(self):
        message: str = 'messages services work'
        print('SERVICE', message)
        return message

    async def create_conversation(self, conversation_info: CreateConversation, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:

            user_id = user.get('id')
            friends = []

            # ------------------------------------------------------------------------
            # BUSCA A LISTA DE AMIGOS RECEBIDOS PARA FAZER A CORRETA INSERÇÃO no GroupMembers
            # buscar lista de amigos reais, pois o usuário pode conseguir mandar algum id de usuário que não está na sua lista

            for id in conversation_info.friends_list:
                user = self.session.query(models.Users).join(
                    models.Friends, models.Users.id == id).filter(models.Friends.owner_id == user_id).first()
                if user:
                    friends.append(user)

            # ------------------------------------------------------------------------
            # se eu tiver só um amigo na lista, então é uma conversa pessoal e utilizo o nome dele na conversation name

            # CASO SEJA UM CHAT PARTICULAR, TENHO QUE VERIFICAR SE JÁ NÃO TENHO UM CHAT CRIADO
            # PRECISO APRIMORAR O CONVERSATION PARA A CRITICA DE CIMA E TAMBÉM PARA ELE RECEBER UMA IMAGME DE GRUPO E MELHORAR A LÓGICA PARA O NOME DA CONVERSATION, VISTO QUE ESTOU USANDO O NOME DO USUÁRIO AMIGO
            # PRECISO ALTERAR, VISTO QUE A CONVERSATION NÃO PODE FICAR COM O NOME DO USUÁRIO, PORQUE UM USER A VERIA O NOME B, MAS O USER B TAMBEM VERIA O NOME B
            # CRIAR UMA CONVERSATION
            conversation_model = models.Conversations()
            conversation_model.converation_name = conversation_info.name
            conversation_model.conversation_type = 0 if len(
                conversation_info.friends_list) == 1 else 1
            self.session.add(conversation_model)
            self.session.commit()

            # ------------------------------------------------------------------------

            member_to_add_to_group = []

            for member in friends:
                member_model = models.GroupMembers()
                member_model.conversation_id = conversation_model.id
                member_model.user_id = member.id
                member_model.joined_datetime = ''
                member_model.left_datetime = ''
                member_to_add_to_group.append(member_model)

            if len(friends):
                # adicionar o usuário atual também no grupo
                current_user_to_group = models.GroupMembers()
                current_user_to_group.conversation_id = conversation_model.id
                current_user_to_group.user_id = user_id
                current_user_to_group.joined_datetime = ''
                current_user_to_group.left_datetime = ''
                member_to_add_to_group.append(current_user_to_group)

                self.session.bulk_save_objects(member_to_add_to_group)
                self.session.commit()

            # ------------------------------------------------------------------------

            # preciso verificar a quantidade de amigos que vou adicionar na minha conversation
            # se for igual a 1 é conversa pessoal
            # se for maior que 1 é conversa em grupo
            # se não tiver nenhum dado tem que retornar mensagem de lista vazia
            # se algum amigo não estiver na lista de amigos, não fazer a inserção do mesmo no grupo
            # se for mensagem pessoal então nem deve criar a mensgem, deve retornar uma mensagem de erro

        return f'{'Grupo' if len(conversation_info.friends_list) == 1 else 'Chat'} iniciado com sucesso!'

    async def get_chat_list(self, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:
            user_id = user.get('id')
            infos = []
            conversations_list = []

            chat_list = self.session.query(models.GroupMembers).filter(
                models.GroupMembers.user_id == user.get('id')).all()

            for chat in chat_list:
                conversation_item = self.session.query(models.Conversations).join(
                    models.GroupMembers, models.Conversations.id == chat.conversation_id).filter(models.GroupMembers.user_id == user_id).first()

                if conversation_item:
                    infos.append(conversation_item)

            for conv in infos:
                participants = [
                    member.user.name for member in conv.groupMember if member.user_id != user_id]

                conversation_name = participants[0] if conv.conversation_type == 0 else conv.conversation_name

                conversations_list.append({
                    "id": conv.id,
                    "conversation_name": conversation_name,
                    "conversation_type": conv.conversation_type,
                    "participants": participants,
                })

            return conversations_list

    async def create_message(self, info: SendMessage, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:

            group_members = self.session.query(models.GroupMembers).filter(
                models.GroupMembers.conversation_id == info.conversation_id).all()

            is_private_chat = self.is_private_chat(group_members)

            message_model = models.Messages()
            message_model.conversation_id = info.conversation_id
            message_model.from_user = info.from_user
            message_model.to_user = info.to_user if is_private_chat else ""
            message_model.message_text = info.message_text
            message_model.sent_datetime = info.sent_datetime

            self.session.add(message_model)
            self.session.commit()

            return message_model

    async def create_message_ws(self, info: SendMessage, token: str):

        user = AuthService(self.session).get_current_user(token=token)
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:
            current_conversation = info.get('conversation_id')
            # print(type(info), 'info here')
            # print(user, 'user information')

            group_members = self.session.query(models.GroupMembers).filter(
                models.GroupMembers.conversation_id == current_conversation).all()

            is_private_chat = self.is_private_chat(group_members)

            message_model = models.Messages()
            message_model.conversation_id = info.get('conversation_id')
            message_model.from_user = info.get('from_user')
            message_model.to_user = info.get(
                'to_user') if is_private_chat else ""
            message_model.message_text = info.get('message_text')
            message_model.sent_datetime = info.get('sent_datetime')

            self.session.add(message_model)
            self.session.commit()

            return message_model

    def is_private_chat(self, infos: list):
        return True if len(infos) == 2 else False
