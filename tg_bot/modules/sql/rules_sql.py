import threading
from typing import Optional, Union

from pymongo import ASCENDING
from sql import db

rules_collection = db["rules"]
INSERTION_LOCK = threading.RLock()


def set_rules(chat_id: Union[int, str], rules_text: str):
    with INSERTION_LOCK:
        chat_id = str(chat_id)
        rules_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"rules": rules_text}},
            upsert=True
        )


def get_rules(chat_id: Union[int, str]) -> Optional[str]:
    chat_id = str(chat_id)
    doc = rules_collection.find_one({"chat_id": chat_id})
    return doc["rules"] if doc else None


def num_chats() -> int:
    return rules_collection.count_documents({})


def migrate_chat(old_chat_id: Union[int, str], new_chat_id: Union[int, str]):
    with INSERTION_LOCK:
        old_id, new_id = str(old_chat_id), str(new_chat_id)

        record = rules_collection.find_one({"chat_id": old_id})
        if record:
            # Replace if the new_chat_id already exists
            rules_collection.replace_one(
                {"chat_id": new_id},
                {"chat_id": new_id, "rules": record["rules"]},
                upsert=True
            )
            rules_collection.delete_one({"chat_id": old_id})
