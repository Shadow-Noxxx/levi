from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

import os

# Path to your SQLite DB
DB_PATH = os.path.join(os.path.dirname(__file__), "levi.sqlite3")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
BASE = declarative_base()

session_factory = sessionmaker(bind=engine)
SESSION = scoped_session(session_factory)

# Import all modules with models BEFORE creating tables
import tg_bot.modules.sql.global_bans_sql  # and other sql modules

# Create all tables
BASE.metadata.create_all(bind=engine)
