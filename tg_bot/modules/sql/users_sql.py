import threading
from typing import Optional, List
from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from tg_bot import dispatcher
from sql import db

users_collection = db["users"]
chats_collection = db["chats"]
chat_members_collection = db["chat_members"]

chat_members_collection.create_index(
    [("chat", ASCENDING), ("user", ASCENDING)], unique=True
)

INSERTION_LOCK = threading.RLock()


def ensure_bot_in_db():
    with INSERTION_LOCK:
        users_collection.update_one(
            {"user_id": dispatcher.bot.id},
            {"$set": {"username": dispatcher.bot.username}},
            upsert=True,
        )


def update_user(user_id: int, username: Optional[str], chat_id: Optional[str] = None, chat_name: Optional[str] = None):
    with INSERTION_LOCK:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"username": username}},
            upsert=True,
        )

        if chat_id and chat_name:
            chats_collection.update_one(
                {"chat_id": str(chat_id)},
                {"$set": {"chat_name": chat_name}},
                upsert=True,
            )
            try:
                chat_members_collection.insert_one({
                    "chat": str(chat_id),
                    "user": user_id
                })
            except DuplicateKeyError:
                pass  # already exists


def get_userid_by_name(username: str) -> List[dict]:
    return list(users_collection.find({"username": {"$regex": f"^{username}$", "$options": "i"}}))


def get_name_by_userid(user_id: int) -> Optional[dict]:
    return users_collection.find_one({"user_id": user_id})


def get_chat_members(chat_id: str) -> List[dict]:
    return list(chat_members_collection.find({"chat": str(chat_id)}))


def get_all_chats() -> List[dict]:
    return list(chats_collection.find())


def get_user_num_chats(user_id: int) -> int:
    return chat_members_collection.count_documents({"user": user_id})


def num_chats() -> int:
    return chats_collection.estimated_document_count()


def num_users() -> int:
    return users_collection.estimated_document_count()


def migrate_chat(old_chat_id: str, new_chat_id: str):
    with INSERTION_LOCK:
        chat = chats_collection.find_one_and_update(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}},
            return_document=ReturnDocument.AFTER
        )

        if chat:
            chat_members = chat_members_collection.find({"chat": str(old_chat_id)})
            for member in chat_members:
                chat_members_collection.update_one(
                    {"_id": member["_id"]},
                    {"$set": {"chat": str(new_chat_id)}}
                )


def del_user(user_id: int) -> bool:
    with INSERTION_LOCK:
        chat_members_collection.delete_many({"user": user_id})
        result = users_collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0
