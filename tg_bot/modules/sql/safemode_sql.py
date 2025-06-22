import threading
from typing import Union
from pymongo.collection import Collection

from sql import db

safemode_collection: Collection = db["safemode"]
SAFEMODE_LOCK = threading.RLock()


def set_safemode(chat_id: Union[int, str], safemode_status: bool = True):
    with SAFEMODE_LOCK:
        chat_id = str(chat_id)
        safemode_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"safemode_status": safemode_status}},
            upsert=True
        )


def is_safemoded(chat_id: Union[int, str]) -> bool:
    chat_id = str(chat_id)
    record = safemode_collection.find_one({"chat_id": chat_id})
    return record["safemode_status"] if record else False

