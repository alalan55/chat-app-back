from sqlalchemy.orm import Session
from typing import Optional
from service.auth import AuthService
from schemas.messages_schema import CreateConversation, SendMessage
import models


class MessageService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session

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

            new_conversation_name = friends[0].name if len(
                conversation_info.friends_list) == 1 else conversation_info.name

            # CASO SEJA UM CHAT PARTICULAR, TENHO QUE VERIFICAR SE JÁ NÃO TENHO UM CHAT CRIADO

            # CRIAR UMA CONVERSATION
            conversation_model = models.Conversations()
            conversation_model.converation_name = new_conversation_name
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

            chat_list = self.session.query(models.GroupMembers).filter(
                models.GroupMembers.user_id == user.get('id')).all()

            for chat in chat_list:
                conversation_item = self.session.query(models.Conversations).join(
                    models.GroupMembers, models.Conversations.id == chat.conversation_id).filter(models.GroupMembers.user_id == user_id).first()

                if conversation_item:
                    infos.append(conversation_item)

            return infos

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

    def is_private_chat(self, infos: list):
        return True if len(infos) == 2 else False
