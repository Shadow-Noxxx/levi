import threading
from sql import db

# MongoDB collections
perm_collection = db["permissions"]
restr_collection = db["restrictions"]

# Locks
PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()


def init_permissions(chat_id, reset=False):
    chat_id = str(chat_id)
    with PERM_LOCK:
        if reset:
            perm_collection.delete_one({"chat_id": chat_id})
        default_perms = {
            "chat_id": chat_id,
            "audio": False,
            "voice": False,
            "contact": False,
            "video": False,
            "videonote": False,
            "document": False,
            "photo": False,
            "sticker": False,
            "gif": False,
            "url": False,
            "bots": False,
            "forward": False,
            "game": False,
            "location": False
        }
        perm_collection.update_one({"chat_id": chat_id}, {"$setOnInsert": default_perms}, upsert=True)
        return perm_collection.find_one({"chat_id": chat_id})


def init_restrictions(chat_id, reset=False):
    chat_id = str(chat_id)
    with RESTR_LOCK:
        if reset:
            restr_collection.delete_one({"chat_id": chat_id})
        default_restr = {
            "chat_id": chat_id,
            "messages": False,
            "media": False,
            "other": False,
            "preview": False
        }
        restr_collection.update_one({"chat_id": chat_id}, {"$setOnInsert": default_restr}, upsert=True)
        return restr_collection.find_one({"chat_id": chat_id})


def update_lock(chat_id, lock_type, locked):
    chat_id = str(chat_id)
    with PERM_LOCK:
        perm_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {lock_type: locked}},
            upsert=True
        )


def update_restriction(chat_id, restr_type, locked):
    chat_id = str(chat_id)
    with RESTR_LOCK:
        if restr_type == "all":
            restr_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {
                    "messages": locked,
                    "media": locked,
                    "other": locked,
                    "preview": locked
                }},
                upsert=True
            )
        else:
            if restr_type == "previews":
                restr_type = "preview"
            restr_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {restr_type: locked}},
                upsert=True
            )


def is_locked(chat_id, lock_type):
    data = perm_collection.find_one({"chat_id": str(chat_id)}, {lock_type: 1})
    return data.get(lock_type, False) if data else False


def is_restr_locked(chat_id, lock_type):
    data = restr_collection.find_one({"chat_id": str(chat_id)})
    if not data:
        return False

    if lock_type == "all":
        return data.get("messages") and data.get("media") and data.get("other") and data.get("preview")
    elif lock_type == "previews":
        return data.get("preview", False)
    else:
        return data.get(lock_type, False)


def get_locks(chat_id):
    return perm_collection.find_one({"chat_id": str(chat_id)})


def get_restr(chat_id):
    return restr_collection.find_one({"chat_id": str(chat_id)})


def migrate_chat(old_chat_id, new_chat_id):
    old_chat_id, new_chat_id = str(old_chat_id), str(new_chat_id)
    with PERM_LOCK:
        old_perm = perm_collection.find_one({"chat_id": old_chat_id})
        if old_perm:
            old_perm["chat_id"] = new_chat_id
            perm_collection.insert_one(old_perm)
            perm_collection.delete_one({"chat_id": old_chat_id})

    with RESTR_LOCK:
        old_restr = restr_collection.find_one({"chat_id": old_chat_id})
        if old_restr:
            old_restr["chat_id"] = new_chat_id
            restr_collection.insert_one(old_restr)
            restr_collection.delete_one({"chat_id": old_chat_id})
