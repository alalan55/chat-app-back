from fastapi import FastAPI
from routes import auth, chat, users
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def health():
    return 'Conectado'
