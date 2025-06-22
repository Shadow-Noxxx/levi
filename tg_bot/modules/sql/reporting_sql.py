import threading
from typing import Union

from sql import db

chat_settings = db["chat_report_settings"]
user_settings = db["user_report_settings"]

CHAT_LOCK = threading.RLock()
USER_LOCK = threading.RLock()


def chat_should_report(chat_id: Union[int, str]) -> bool:
    result = chat_settings.find_one({"chat_id": str(chat_id)})
    return result.get("should_report", False) if result else False


def user_should_report(user_id: int) -> bool:
    result = user_settings.find_one({"user_id": user_id})
    return result.get("should_report", True) if result else True


def set_chat_setting(chat_id: Union[int, str], setting: bool):
    with CHAT_LOCK:
        chat_settings.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"should_report": setting}},
            upsert=True
        )


def set_user_setting(user_id: int, setting: bool):
    with USER_LOCK:
        user_settings.update_one(
            {"user_id": user_id},
            {"$set": {"should_report": setting}},
            upsert=True
        )


def migrate_chat(old_chat_id: Union[int, str], new_chat_id: Union[int, str]):
    with CHAT_LOCK:
        old_id = str(old_chat_id)
        new_id = str(new_chat_id)

        old_record = chat_settings.find_one({"chat_id": old_id})
        if old_record:
            chat_settings.delete_one({"chat_id": new_id})  # prevent PK conflict
            chat_settings.update_one(
                {"chat_id": old_id},
                {"$set": {"chat_id": new_id}}
            )
