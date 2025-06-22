import threading
from typing import Optional
from pymongo.collection import Collection

from sql import db

userinfo_collection: Collection = db["userinfo"]
userbio_collection: Collection = db["userbio"]

INSERTION_LOCK = threading.RLock()


def get_user_me_info(user_id: int) -> Optional[str]:
    record = userinfo_collection.find_one({"user_id": user_id})
    return record["info"] if record else None


def set_user_me_info(user_id: int, info: str):
    with INSERTION_LOCK:
        userinfo_collection.update_one(
            {"user_id": user_id},
            {"$set": {"info": info}},
            upsert=True
        )


def get_user_bio(user_id: int) -> Optional[str]:
    record = userbio_collection.find_one({"user_id": user_id})
    return record["bio"] if record else None


def set_user_bio(user_id: int, bio: str):
    with INSERTION_LOCK:
        userbio_collection.update_one(
            {"user_id": user_id},
            {"$set": {"bio": bio}},
            upsert=True
        )


def clear_user_info(user_id: int) -> bool:
    with INSERTION_LOCK:
        result = userinfo_collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0


def clear_user_bio(user_id: int) -> bool:
    with INSERTION_LOCK:
        result = userbio_collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0
