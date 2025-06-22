import threading
from sql import db

# Use MongoDB collection
afk_collection = db["afk_users"]

INSERTION_LOCK = threading.RLock()
AFK_USERS = {}

# ✅ Check if user is AFK (in-memory check)
def is_afk(user_id):
    return user_id in AFK_USERS

# ✅ Check status and reason
def check_afk_status(user_id):
    if user_id in AFK_USERS:
        return True, AFK_USERS[user_id]
    return False, ""

# ✅ Set user AFK
def set_afk(user_id, reason=""):
    with INSERTION_LOCK:
        afk_collection.update_one(
            {"user_id": user_id},
            {"$set": {"is_afk": True, "reason": reason}},
            upsert=True,
        )
        AFK_USERS[user_id] = reason

# ✅ Remove AFK status
def rm_afk(user_id):
    with INSERTION_LOCK:
        result = afk_collection.delete_one({"user_id": user_id})
        if user_id in AFK_USERS:
            del AFK_USERS[user_id]
        return result.deleted_count > 0

# ✅ Load existing AFK users into memory on startup
def __load_afk_users():
    global AFK_USERS
    afk_data = afk_collection.find({"is_afk": True})
    AFK_USERS = {entry["user_id"]: entry.get("reason", "") for entry in afk_data}

__load_afk_users()
