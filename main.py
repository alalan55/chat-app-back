from fastapi import FastAPI
from routes import auth, chat, users, messages
from routes.messages import lifespan
from fastapi.middleware.cors import CORSMiddleware
from broadcaster import Broadcast

# https://pypi.org/project/broadcaster/


broadcast = Broadcast('memory://chat.db')

# app = FastAPI(on_startup=[broadcast.connect],
#               on_shutdown=[broadcast.disconnect], lifespan=lifespan)

app = FastAPI(lifespan=lifespan)


app.include_router(auth.router)
# app.include_router(chat.router)
app.include_router(users.router)
app.include_router(messages.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def health():
    return 'Conectado'
