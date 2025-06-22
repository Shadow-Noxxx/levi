import threading
from pymongo import ASCENDING
from sql import db

# MongoDB collection
log_collection = db["log_channels"]

# Thread lock for thread safety
LOGS_INSERTION_LOCK = threading.RLock()

# In-memory cache
CHANNELS = {}


def set_chat_log_channel(chat_id, log_channel):
    chat_id = str(chat_id)
    log_channel = str(log_channel)
    with LOGS_INSERTION_LOCK:
        log_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"log_channel": log_channel}},
            upsert=True
        )
        CHANNELS[chat_id] = log_channel


def get_chat_log_channel(chat_id):
    return CHANNELS.get(str(chat_id))


def stop_chat_logging(chat_id):
    chat_id = str(chat_id)
    with LOGS_INSERTION_LOCK:
        result = log_collection.find_one({"chat_id": chat_id})
        if result:
            log_collection.delete_one({"chat_id": chat_id})
            return CHANNELS.pop(chat_id, None)
        return None


def num_logchannels():
    return log_collection.count_documents({})


def migrate_chat(old_chat_id, new_chat_id):
    old_chat_id = str(old_chat_id)
    new_chat_id = str(new_chat_id)
    with LOGS_INSERTION_LOCK:
        old = log_collection.find_one({"chat_id": old_chat_id})
        if old:
            log_channel = old.get("log_channel")
            log_collection.insert_one({"chat_id": new_chat_id, "log_channel": log_channel})
            log_collection.delete_one({"chat_id": old_chat_id})

            if old_chat_id in CHANNELS:
                CHANNELS[new_chat_id] = CHANNELS.pop(old_chat_id)


def __load_log_channels():
    global CHANNELS
    all_logs = log_collection.find({})
    CHANNELS = {log["chat_id"]: log["log_channel"] for log in all_logs}


# Load log channels into cache on startup
__load_log_channels()
