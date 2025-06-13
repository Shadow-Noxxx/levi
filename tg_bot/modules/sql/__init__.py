import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# Path to SQLite DB file (you can change it to a full path if needed)
DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite")

# Create SQLite engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Declare Base and Session
BASE = declarative_base()
SESSION = scoped_session(sessionmaker(bind=engine, autoflush=False))

# Import all models that define tables before calling create_all
# (to ensure all tables are registered with BASE)
import tg_bot.modules.sql.global_bans_sql  # Add more as needed

# Create all tables (if they don't exist)
BASE.metadata.create_all(bind=engine)
