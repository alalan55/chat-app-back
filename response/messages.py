from typing import Optional


def successful_response(status_code: int, token: Optional[str] = None, content: Optional[dict] = None, message: Optional[str] = None):
    return {
        "status": status_code,
        "message": message,
        "content": content,
        "token": token
    }


# def get_user_exception():
#     credential_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED, detail="Não foi possível validar as credenciais", headers={"WWW-Authenticate": "Bearer"})
#     return credential_exception
