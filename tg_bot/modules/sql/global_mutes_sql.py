import threading
from sql import db

# MongoDB collections
gmutes_collection = db["gmutes"]
gmute_settings_collection = db["gmute_settings"]

# Thread-safe locks
GMUTED_USERS_LOCK = threading.RLock()
GMUTE_SETTING_LOCK = threading.RLock()

# In-memory cache
GMUTED_LIST = set()
GMUTESTAT_LIST = set()

# ✅ Add or update a globally muted user
def gmute_user(user_id, name, reason=None):
    with GMUTED_USERS_LOCK:
        gmutes_collection.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "reason": reason}},
            upsert=True
        )
        __load_gmuted_userid_list()

# ✅ Update only the reason
def update_gmute_reason(user_id, name, reason=None):
    with GMUTED_USERS_LOCK:
        result = gmutes_collection.find_one({"user_id": user_id})
        if not result:
            return False
        gmutes_collection.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "reason": reason}}
        )
        return True

# ✅ Remove a globally muted user
def ungmute_user(user_id):
    with GMUTED_USERS_LOCK:
        gmutes_collection.delete_one({"user_id": user_id})
        __load_gmuted_userid_list()

# ✅ Check if a user is globally muted
def is_user_gmuted(user_id):
    return user_id in GMUTED_LIST

# ✅ Get a specific gmute entry
def get_gmuted_user(user_id):
    return gmutes_collection.find_one({"user_id": user_id})

# ✅ Get full list of gmutes
def get_gmute_list():
    return list(gmutes_collection.find({}, {"_id": 0}))

# ✅ Enable gmutes for a chat
def enable_gmutes(chat_id):
    with GMUTE_SETTING_LOCK:
        gmute_settings_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"setting": True}},
            upsert=True
        )
        GMUTESTAT_LIST.discard(str(chat_id))

# ✅ Disable gmutes for a chat
def disable_gmutes(chat_id):
    with GMUTE_SETTING_LOCK:
        gmute_settings_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"setting": False}},
            upsert=True
        )
        GMUTESTAT_LIST.add(str(chat_id))

# ✅ Check if a chat honors gmutes
def does_chat_gmute(chat_id):
    return str(chat_id) not in GMUTESTAT_LIST

# ✅ Number of currently globally muted users
def num_gmuted_users():
    return len(GMUTED_LIST)

# ✅ Migration of gmute setting to new chat ID
def migrate_chat(old_chat_id, new_chat_id):
    with GMUTE_SETTING_LOCK:
        old = gmute_settings_collection.find_one({"chat_id": str(old_chat_id)})
        if old:
            gmute_settings_collection.update_one(
                {"chat_id": str(new_chat_id)},
                {"$set": {"setting": old.get("setting", True)}},
                upsert=True
            )
            gmute_settings_collection.delete_one({"chat_id": str(old_chat_id)})

# ✅ Load gmutes into memory
def __load_gmuted_userid_list():
    global GMUTED_LIST
    GMUTED_LIST = {x["user_id"] for x in gmutes_collection.find({}, {"user_id": 1})}

# ✅ Load chats where gmutes are disabled
def __load_gmute_stat_list():
    global GMUTESTAT_LIST
    GMUTESTAT_LIST = {
        x["chat_id"] for x in gmute_settings_collection.find({"setting": False}, {"chat_id": 1})
    }

# ✅ Initialize on startup
__load_gmuted_userid_list()
__load_gmute_stat_list()
