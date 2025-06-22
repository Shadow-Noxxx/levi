import threading
from typing import Optional, Tuple, List
from pymongo import ReturnDocument

from sql import db

warns_col = db["warns"]
warn_filters_col = db["warn_filters"]
warn_settings_col = db["warn_settings"]

# Locks
WARN_INSERTION_LOCK = threading.RLock()
WARN_FILTER_INSERTION_LOCK = threading.RLock()
WARN_SETTINGS_LOCK = threading.RLock()

# Cache
WARN_FILTERS: dict[str, List[str]] = {}


# Warn Management
def warn_user(user_id: int, chat_id: str, reason: Optional[str] = None) -> Tuple[int, List[str]]:
    with WARN_INSERTION_LOCK:
        record = warns_col.find_one({"user_id": user_id, "chat_id": chat_id}) or {
            "user_id": user_id,
            "chat_id": chat_id,
            "num_warns": 0,
            "reasons": []
        }

        record["num_warns"] += 1
        if reason:
            record["reasons"].append(reason)

        warns_col.replace_one({"user_id": user_id, "chat_id": chat_id}, record, upsert=True)
        return record["num_warns"], record["reasons"]


def remove_warn(user_id: int, chat_id: str) -> bool:
    with WARN_INSERTION_LOCK:
        record = warns_col.find_one({"user_id": user_id, "chat_id": chat_id})
        if record and record["num_warns"] > 0:
            record["num_warns"] -= 1
            warns_col.replace_one({"user_id": user_id, "chat_id": chat_id}, record)
            return True
        return False


def reset_warns(user_id: int, chat_id: str):
    with WARN_INSERTION_LOCK:
        warns_col.update_one(
            {"user_id": user_id, "chat_id": chat_id},
            {"$set": {"num_warns": 0, "reasons": []}}
        )


def get_warns(user_id: int, chat_id: str) -> Optional[Tuple[int, List[str]]]:
    record = warns_col.find_one({"user_id": user_id, "chat_id": chat_id})
    return (record["num_warns"], record["reasons"]) if record else None


# Warn Filters
def add_warn_filter(chat_id: str, keyword: str, reply: str):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filters_col.update_one(
            {"chat_id": chat_id, "keyword": keyword},
            {"$set": {"reply": reply}},
            upsert=True
        )
        WARN_FILTERS.setdefault(chat_id, [])
        if keyword not in WARN_FILTERS[chat_id]:
            WARN_FILTERS[chat_id].append(keyword)
            WARN_FILTERS[chat_id] = sorted(set(WARN_FILTERS[chat_id]), key=lambda x: (-len(x), x))


def remove_warn_filter(chat_id: str, keyword: str) -> bool:
    with WARN_FILTER_INSERTION_LOCK:
        result = warn_filters_col.delete_one({"chat_id": chat_id, "keyword": keyword})
        if result.deleted_count:
            WARN_FILTERS.get(chat_id, []).remove(keyword)
            return True
        return False


def get_chat_warn_triggers(chat_id: str) -> List[str]:
    return WARN_FILTERS.get(chat_id, [])


def get_chat_warn_filters(chat_id: str) -> List[dict]:
    return list(warn_filters_col.find({"chat_id": chat_id}))


def get_warn_filter(chat_id: str, keyword: str) -> Optional[dict]:
    return warn_filters_col.find_one({"chat_id": chat_id, "keyword": keyword})


# Settings
def set_warn_limit(chat_id: str, warn_limit: int):
    with WARN_SETTINGS_LOCK:
        warn_settings_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"warn_limit": warn_limit}},
            upsert=True
        )


def set_warn_strength(chat_id: str, soft_warn: bool):
    with WARN_SETTINGS_LOCK:
        warn_settings_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"soft_warn": soft_warn}},
            upsert=True
        )


def get_warn_setting(chat_id: str) -> Tuple[int, bool]:
    setting = warn_settings_col.find_one({"chat_id": chat_id})
    return (setting.get("warn_limit", 3), setting.get("soft_warn", False)) if setting else (3, False)


# Stats
def num_warns() -> int:
    result = warns_col.aggregate([{"$group": {"_id": None, "total": {"$sum": "$num_warns"}}}])
    return next(result, {}).get("total", 0)


def num_warn_chats() -> int:
    return len(warns_col.distinct("chat_id"))


def num_warn_filters() -> int:
    return warn_filters_col.count_documents({})


def num_warn_chat_filters(chat_id: str) -> int:
    return warn_filters_col.count_documents({"chat_id": chat_id})


def num_warn_filter_chats() -> int:
    return len(warn_filters_col.distinct("chat_id"))


# Migration
def migrate_chat(old_chat_id: str, new_chat_id: str):
    with WARN_INSERTION_LOCK:
        warns_col.update_many({"chat_id": old_chat_id}, {"$set": {"chat_id": new_chat_id}})
    with WARN_FILTER_INSERTION_LOCK:
        warn_filters_col.update_many({"chat_id": old_chat_id}, {"$set": {"chat_id": new_chat_id}})
        if old_chat_id in WARN_FILTERS:
            WARN_FILTERS[new_chat_id] = WARN_FILTERS.pop(old_chat_id)
    with WARN_SETTINGS_LOCK:
        warn_settings_col.update_many({"chat_id": old_chat_id}, {"$set": {"chat_id": new_chat_id}})


# Initial Load
def __load_chat_warn_filters():
    global WARN_FILTERS
    for filt in warn_filters_col.find():
        WARN_FILTERS.setdefault(filt["chat_id"], []).append(filt["keyword"])
    for cid in WARN_FILTERS:
        WARN_FILTERS[cid] = sorted(set(WARN_FILTERS[cid]), key=lambda i: (-len(i), i))


__load_chat_warn_filters()
