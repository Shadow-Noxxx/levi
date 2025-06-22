import threading
from sql import db

# MongoDB collection
disable_collection = db["disabled_commands"]

DISABLE_INSERTION_LOCK = threading.RLock()
DISABLED = {}

# ✅ Disable a command for a chat
def disable_command(chat_id, disable):
    with DISABLE_INSERTION_LOCK:
        exists = disable_collection.find_one({"chat_id": str(chat_id), "command": disable})
        if not exists:
            disable_collection.insert_one({"chat_id": str(chat_id), "command": disable})
            DISABLED.setdefault(str(chat_id), set()).add(disable)
            return True
        return False

# ✅ Enable (remove) a command for a chat
def enable_command(chat_id, enable):
    with DISABLE_INSERTION_LOCK:
        result = disable_collection.delete_one({"chat_id": str(chat_id), "command": enable})
        if result.deleted_count:
            DISABLED.get(str(chat_id), set()).discard(enable)
            return True
        return False

# ✅ Check if a command is disabled
def is_command_disabled(chat_id, cmd):
    return cmd in DISABLED.get(str(chat_id), set())

# ✅ Get all disabled commands for a chat
def get_all_disabled(chat_id):
    return DISABLED.get(str(chat_id), set())

# ✅ Count number of unique chats with disabled commands
def num_chats():
    return len(disable_collection.distinct("chat_id"))

# ✅ Count total number of disabled commands
def num_disabled():
    return disable_collection.count_documents({})

# ✅ Migrate disabled commands from old chat to new chat
def migrate_chat(old_chat_id, new_chat_id):
    with DISABLE_INSERTION_LOCK:
        old_id = str(old_chat_id)
        new_id = str(new_chat_id)
        commands = disable_collection.find({"chat_id": old_id})

        for cmd in commands:
            disable_collection.update_one(
                {"chat_id": new_id, "command": cmd["command"]},
                {"$set": {"chat_id": new_id, "command": cmd["command"]}},
                upsert=True
            )

        disable_collection.delete_many({"chat_id": old_id})

        if old_id in DISABLED:
            DISABLED[new_id] = DISABLED.get(old_id, set())
            del DISABLED[old_id]

# ✅ Load all disabled commands into memory on startup
def __load_disabled_commands():
    global DISABLED
    all_data = disable_collection.find()
    for entry in all_data:
        DISABLED.setdefault(entry["chat_id"], set()).add(entry["command"])

__load_disabled_commands()
