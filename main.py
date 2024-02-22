# 1 Usuario deve se conectar
# 1.2 nome, email, senha, foto de perfil, id, shared_id(automatico
# 2 Usuário pode adicionar usuários na sua lista de amigos atraves do shared_id
# 3 Usuário pode mandar mensavem individual para esse shared_id
# 4 Usuário pode criar grupo e adicionar amigos nele

from fastapi import FastAPI
from routes import auth, chat


app = FastAPI()

app.include_router(auth.router)
app.include_router(chat.router)


@app.get('/')
async def health():
    return 'Conectado'
