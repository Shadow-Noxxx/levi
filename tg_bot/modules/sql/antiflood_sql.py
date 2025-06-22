import threading
from sql import db

# MongoDB collection
flood_collection = db["antiflood"]

DEF_COUNT = 0
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)

INSERTION_LOCK = threading.RLock()
CHAT_FLOOD = {}

# ✅ Set flood limit for a chat
def set_flood(chat_id, amount):
    with INSERTION_LOCK:
        flood_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"user_id": None, "limit": amount}},
            upsert=True,
        )
        CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)

# ✅ Check/update message count, return True if flood threshold exceeded
def update_flood(chat_id: str, user_id) -> bool:
    if str(chat_id) in CHAT_FLOOD:
        curr_user_id, count, limit = CHAT_FLOOD.get(str(chat_id), DEF_OBJ)

        if limit == 0:
            return False

        if user_id != curr_user_id or user_id is None:
            CHAT_FLOOD[str(chat_id)] = (user_id, DEF_COUNT + 1, limit)
            return False

        count += 1
        if count > limit:
            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, limit)
            return True

        CHAT_FLOOD[str(chat_id)] = (user_id, count, limit)
        return False

# ✅ Get flood limit for a chat
def get_flood_limit(chat_id):
    return CHAT_FLOOD.get(str(chat_id), DEF_OBJ)[2]

# ✅ Migrate chat ID (e.g., after group ID change)
def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        data = flood_collection.find_one({"chat_id": str(old_chat_id)})
        if data:
            flood_collection.update_one(
                {"chat_id": str(new_chat_id)},
                {"$set": {"limit": data.get("limit", DEF_LIMIT), "user_id": None}},
                upsert=True
            )
            CHAT_FLOOD[str(new_chat_id)] = CHAT_FLOOD.get(str(old_chat_id), DEF_OBJ)

# ✅ Load all flood configs into memory
def __load_flood_settings():
    global CHAT_FLOOD
    all_chats = flood_collection.find()
    CHAT_FLOOD = {
        chat["chat_id"]: (None, DEF_COUNT, chat.get("limit", DEF_LIMIT))
        for chat in all_chats
    }

__load_flood_settings()
