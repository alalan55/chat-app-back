from sqlalchemy.orm import Session
from typing import Optional
from service.auth import AuthService
from schemas.messages_schema import CreateConversation
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

            # ------------------------------------------------------------------------

            # CRIAR UMA CONVERSATION
            conversation_model = models.Conversations()
            conversation_model.converation_name = conversation_info.name
            self.session.add(conversation_model)
            self.session.commit()

            # ------------------------------------------------------------------------

            # BUSCA A LISTA DE AMIGOS RECEBIDOS PARA FAZER A CORRETA INSERÇÃO no GroupMembers

            # user_to_add_is_on_list = self.session.query(models.Friends).filter(
            #     models.Friends.friend_id == user_to_add.shared_id).first()

            friends = []
            member_to_add_to_group = []

            # buscar lista de amigos reais, pois o usuário pode conseguir mandar algum id de usuário que não está na sua lista
            for id in conversation_info.friends_list:
                user = self.session.query(models.Users).join(
                    models.Friends, models.Users.id == id).filter(models.Friends.owner_id == user_id).first()

                if user:
                    friends.append(user)

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

        return 'MENSAGEM DO SERVICE'

    async def get_chat_list(self, user: dict):
        user_is_valid = AuthService(self.session).user_is_validated(user)

        if user_is_valid:
            chat_list = self.session.query(models.GroupMembers).filter(models.GroupMembers.user_id == user.get('id')).all()

            print(chat_list, 'here')

            return chat_list