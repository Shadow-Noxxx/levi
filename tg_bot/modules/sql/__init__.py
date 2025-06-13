import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# Define DB path — you can change it if needed
DB_PATH = os.path.join(os.path.dirname(__file__), "levi.sqlite3")

# Initialize engine and base
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
BASE = declarative_base()

# Create session
session_factory = sessionmaker(bind=engine)
SESSION = scoped_session(session_factory)

# ❗️Import your model modules BEFORE creating tables
# This ensures SQLAlchemy is aware of all defined models
import tg_bot.modules.sql.global_bans_sql  # 👈 Important!
# import other SQL modules here if any...

# ✅ Create all tables now
BASE.metadata.create_all(bind=engine)
