import threading
from typing import List

from sqlalchemy import Column, UnicodeText, Integer

from tg_bot.modules.sql import BASE, SESSION


class RSS(BASE):
    __tablename__ = "rss_feed"

    id = Column(Integer, primary_key=True)
    chat_id = Column(UnicodeText, nullable=False)
    feed_link = Column(UnicodeText)
    old_entry_link = Column(UnicodeText)

    def __init__(self, chat_id: str, feed_link: str, old_entry_link: str):
        self.chat_id = chat_id
        self.feed_link = feed_link
        self.old_entry_link = old_entry_link

    def __repr__(self):
        return f"<RSS chat_id={self.chat_id} feed={self.feed_link} old={self.old_entry_link}>"


INSERTION_LOCK = threading.RLock()


def check_url_availability(chat_id: str, feed_link: str) -> List[RSS]:
    try:
        return SESSION.query(RSS).filter_by(chat_id=chat_id, feed_link=feed_link).all()
    finally:
        SESSION.close()


def add_url(chat_id: str, feed_link: str, old_entry_link: str):
    with INSERTION_LOCK:
        entry = RSS(chat_id, feed_link, old_entry_link)
        SESSION.add(entry)
        SESSION.commit()


def remove_url(chat_id: str, feed_link: str):
    with INSERTION_LOCK:
        rows = check_url_availability(chat_id, feed_link)
        for row in rows:
            SESSION.delete(row)
        SESSION.commit()


def get_urls(chat_id: str) -> List[RSS]:
    try:
        return SESSION.query(RSS).filter_by(chat_id=chat_id).all()
    finally:
        SESSION.close()


def get_all() -> List[RSS]:
    try:
        return SESSION.query(RSS).all()
    finally:
        SESSION.close()


def update_url(row_id: int, new_entry_link: str):
    with INSERTION_LOCK:
        row = SESSION.query(RSS).get(row_id)
        if row:
            row.old_entry_link = new_entry_link
            SESSION.commit()
