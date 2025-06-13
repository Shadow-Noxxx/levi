import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# Path to SQLite DB file
DB_PATH = os.path.join(os.path.dirname(__file__), "levi.sqlite3")

# SQLAlchemy engine and base
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
BASE = declarative_base()

# Session factory
session_factory = sessionmaker(bind=engine)
SESSION = scoped_session(session_factory)

# Import all model modules to register tables
# IMPORTANT: Do not skip any
import tg_bot.modules.sql.afk_sql
import tg_bot.modules.sql.antiflood_sql
import tg_bot.modules.sql.blacklist_sql
import tg_bot.modules.sql.cust_filters_sql
import tg_bot.modules.sql.disable_sql
import tg_bot.modules.sql.global_bans_sql
import tg_bot.modules.sql.global_mutes_sql
import tg_bot.modules.sql.locks_sql
import tg_bot.modules.sql.log_channel_sql
import tg_bot.modules.sql.notes_sql
import tg_bot.modules.sql.reporting_sql
import tg_bot.modules.sql.rss_sql
import tg_bot.modules.sql.rules_sql
import tg_bot.modules.sql.safemode_sql
import tg_bot.modules.sql.userinfo_sql
import tg_bot.modules.sql.users_sql
import tg_bot.modules.sql.warns_sql
import tg_bot.modules.sql.welcome_sql

# Finally, create tables
BASE.metadata.create_all(bind=engine)
