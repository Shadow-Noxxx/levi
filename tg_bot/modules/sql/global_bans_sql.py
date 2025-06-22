import threading
from sql import db

# MongoDB collections
gbans_collection = db["gbans"]
gban_settings_collection = db["gban_settings"]

# Locks
GBANNED_USERS_LOCK = threading.RLock()
GBAN_SETTING_LOCK = threading.RLock()

# In-memory caches
GBANNED_LIST = set()
GBANSTAT_LIST = set()

# ✅ Gban a user
def gban_user(user_id, name, reason=None):
    with GBANNED_USERS_LOCK:
        gbans_collection.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "reason": reason}},
            upsert=True
        )
        __load_gbanned_userid_list()

# ✅ Update gban reason
def update_gban_reason(user_id, name, reason=None):
    with GBANNED_USERS_LOCK:
        old = gbans_collection.find_one({"user_id": user_id})
        if not old:
            return None
        gbans_collection.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "reason": reason}},
        )
        return old.get("reason")

# ✅ Ungban a user
def ungban_user(user_id):
    with GBANNED_USERS_LOCK:
        gbans_collection.delete_one({"user_id": user_id})
        __load_gbanned_userid_list()

# ✅ Check if user is gbanned
def is_user_gbanned(user_id):
    return user_id in GBANNED_LIST

# ✅ Get full gban entry for a user
def get_gbanned_user(user_id):
    return gbans_collection.find_one({"user_id": user_id})

# ✅ Get list of all gbanned users
def get_gban_list():
    return list(gbans_collection.find({}, {"_id": 0}))

# ✅ Enable gban enforcement in a chat
def enable_gbans(chat_id):
    with GBAN_SETTING_LOCK:
        gban_settings_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"setting": True}},
            upsert=True
        )
        GBANSTAT_LIST.discard(str(chat_id))

# ✅ Disable gban enforcement in a chat
def disable_gbans(chat_id):
    with GBAN_SETTING_LOCK:
        gban_settings_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"setting": False}},
            upsert=True
        )
        GBANSTAT_LIST.add(str(chat_id))

# ✅ Check if chat enforces gbans
def does_chat_gban(chat_id):
    return str(chat_id) not in GBANSTAT_LIST

# ✅ Count number of gbanned users
def num_gbanned_users():
    return len(GBANNED_LIST)

# ✅ Migrate settings to a new chat ID
def migrate_chat(old_chat_id, new_chat_id):
    with GBAN_SETTING_LOCK:
        old = gban_settings_collection.find_one({"chat_id": str(old_chat_id)})
        if old:
            gban_settings_collection.update_one(
                {"chat_id": str(new_chat_id)},
                {"$set": {"setting": old.get("setting", True)}},
                upsert=True
            )
            gban_settings_collection.delete_one({"chat_id": str(old_chat_id)})

# ✅ Load gbanned user IDs into memory
def __load_gbanned_userid_list():
    global GBANNED_LIST
    GBANNED_LIST = {x["user_id"] for x in gbans_collection.find({}, {"user_id": 1})}

# ✅ Load chats with gban disabled
def __load_gban_stat_list():
    global GBANSTAT_LIST
    chats = gban_settings_collection.find({"setting": False}, {"chat_id": 1})
    GBANSTAT_LIST = {x["chat_id"] for x in chats}

# ✅ Preload on startup
__load_gbanned_userid_list()
__load_gban_stat_list()
