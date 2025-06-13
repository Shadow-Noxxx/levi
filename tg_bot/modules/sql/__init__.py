from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os

# SQLite file path (it will create a file named bot_data.db in your project root)
DB_URI = "sqlite:///bot_data.db"

BASE = declarative_base()

def start() -> scoped_session:
    engine = create_engine(DB_URI, echo=False)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))

SESSION = start()
