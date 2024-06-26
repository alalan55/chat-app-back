from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DB_URL = 'sqlite:///./chat.db'

# engine = create_engine(SQLALCHEMY_DB_URL, connect_args={
#                        'check_same_thread': False}, pool_size=20, max_overflow=0)

engine = create_engine(SQLALCHEMY_DB_URL, connect_args={
                       'check_same_thread': False})


SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()
