import os
from pymongo import MongoClient

# Get MongoDB URI from environment variable or fallback to local DB
MONGO_URI = os.environ.get("MONGO_DB_URI", "mongodb://localhost:27017")

# Create a MongoDB client
client = MongoClient(MONGO_URI)

# Choose the database (you can rename 'levi_bot' if needed)
db = client["levi_bot"]

# Exported DB object can be used in each module
# Example use in another file: from sql import db
# Then use: db["collection_name"].find_one(...)

# Import all model modules to register usage
# Ensure each module now uses: `from sql import db` to access the database
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
