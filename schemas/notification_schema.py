import enum


class NotificationType(enum.Enum):
    ON_NEW_MESSAGE = 1
    ON_NEW_CONVERSATION = 2
    ON_NEW_GROUP = 3
    ON_NEW_PRIVATE_CHAT = 4
    ON_ADD_ON_GROUP = 5
  
