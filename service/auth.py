from routes.auth import get_user_exception
from sqlalchemy.orm import Session
from routes.auth import get_user_exception

import models


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def user_is_validated(self, user: dict):

        if user is None:
            return False
        else:
            return True
