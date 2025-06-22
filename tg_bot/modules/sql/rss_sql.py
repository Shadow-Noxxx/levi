import threading
from typing import List, Dict

from bson.objectid import ObjectId
from sql import db

rss_collection = db["rss_feed"]
INSERTION_LOCK = threading.RLock()


def check_url_availability(chat_id: str, feed_link: str) -> List[Dict]:
    return list(rss_collection.find({"chat_id": chat_id, "feed_link": feed_link}))


def add_url(chat_id: str, feed_link: str, old_entry_link: str):
    with INSERTION_LOCK:
        rss_collection.insert_one({
            "chat_id": chat_id,
            "feed_link": feed_link,
            "old_entry_link": old_entry_link
        })


def remove_url(chat_id: str, feed_link: str):
    with INSERTION_LOCK:
        rss_collection.delete_many({"chat_id": chat_id, "feed_link": feed_link})


def get_urls(chat_id: str) -> List[Dict]:
    return list(rss_collection.find({"chat_id": chat_id}))


def get_all() -> List[Dict]:
    return list(rss_collection.find({}))


def update_url(row_id: str, new_entry_link: str):
    with INSERTION_LOCK:
        rss_collection.update_one(
            {"_id": ObjectId(row_id)},
            {"$set": {"old_entry_link": new_entry_link}}
        )
