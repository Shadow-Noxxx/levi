import threading
from sql import db

# MongoDB collection
blacklist_collection = db["blacklist"]

BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()
CHAT_BLACKLISTS = {}

# ✅ Add a trigger to blacklist
def add_to_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_collection.update_one(
            {"chat_id": str(chat_id), "trigger": trigger},
            {"$set": {"chat_id": str(chat_id), "trigger": trigger}},
            upsert=True,
        )
        CHAT_BLACKLISTS.setdefault(str(chat_id), set()).add(trigger)

# ✅ Remove a trigger from blacklist
def rm_from_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        result = blacklist_collection.delete_one({"chat_id": str(chat_id), "trigger": trigger})
        if result.deleted_count:
            CHAT_BLACKLISTS.get(str(chat_id), set()).discard(trigger)
            return True
        return False

# ✅ Get set of blacklisted triggers for a chat
def get_chat_blacklist(chat_id):
    return CHAT_BLACKLISTS.get(str(chat_id), set())

# ✅ Count total number of blacklist filters across all chats
def num_blacklist_filters():
    return blacklist_collection.count_documents({})

# ✅ Count blacklist filters in one specific chat
def num_blacklist_chat_filters(chat_id):
    return blacklist_collection.count_documents({"chat_id": str(chat_id)})

# ✅ Count how many unique chats have blacklist filters
def num_blacklist_filter_chats():
    return len(blacklist_collection.distinct("chat_id"))

# ✅ Migrate blacklist data from old chat ID to new one
def migrate_chat(old_chat_id, new_chat_id):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        old_id = str(old_chat_id)
        new_id = str(new_chat_id)

        # Copy entries to new chat_id
        entries = blacklist_collection.find({"chat_id": old_id})
        for entry in entries:
            blacklist_collection.update_one(
                {"chat_id": new_id, "trigger": entry["trigger"]},
                {"$set": {"chat_id": new_id, "trigger": entry["trigger"]}},
                upsert=True
            )

        # Remove old entries
        blacklist_collection.delete_many({"chat_id": old_id})

        # Update in-memory cache
        CHAT_BLACKLISTS[new_id] = CHAT_BLACKLISTS.get(old_id, set())
        if old_id in CHAT_BLACKLISTS:
            del CHAT_BLACKLISTS[old_id]

# ✅ Load all blacklisted triggers into memory on startup
def __load_chat_blacklists():
    global CHAT_BLACKLISTS
    all_filters = blacklist_collection.find()
    temp = {}
    for entry in all_filters:
        chat_id = entry["chat_id"]
        trigger = entry["trigger"]
        temp.setdefault(chat_id, []).append(trigger)
    CHAT_BLACKLISTS = {x: set(y) for x, y in temp.items()}

__load_chat_blacklists()
