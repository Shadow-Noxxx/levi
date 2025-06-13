import threading
from typing import Optional, Union

from sqlalchemy import Column, String, UnicodeText, func, distinct

from tg_bot.modules.sql import SESSION, BASE


class Rules(BASE):
    __tablename__ = "rules"

    chat_id = Column(String(14), primary_key=True)
    rules = Column(UnicodeText, default="")

    def __init__(self, chat_id: Union[int, str]):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return f"<Rules chat_id={self.chat_id} rules={self.rules[:30]}...>"


INSERTION_LOCK = threading.RLock()


def set_rules(chat_id: Union[int, str], rules_text: str):
    with INSERTION_LOCK:
        chat_id = str(chat_id)
        record = SESSION.query(Rules).get(chat_id)
        if not record:
            record = Rules(chat_id)

        record.rules = rules_text
        SESSION.add(record)
        SESSION.commit()


def get_rules(chat_id: Union[int, str]) -> Optional[str]:
    try:
        chat_id = str(chat_id)
        record = SESSION.query(Rules).get(chat_id)
        return record.rules if record else None
    finally:
        SESSION.close()


def num_chats() -> int:
    try:
        return SESSION.query(func.count(distinct(Rules.chat_id))).scalar()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id: Union[int, str], new_chat_id: Union[int, str]):
    with INSERTION_LOCK:
        record = SESSION.query(Rules).get(str(old_chat_id))
        if record:
            # Avoid PK conflict if new_chat_id already exists
            SESSION.query(Rules).filter_by(chat_id=str(new_chat_id)).delete()

            record.chat_id = str(new_chat_id)
            SESSION.commit()
