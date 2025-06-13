import threading
from typing import Union

from sqlalchemy import Column, String, Boolean

from tg_bot.modules.sql import SESSION, BASE


class Safemode(BASE):
    __tablename__ = "safemode"
    chat_id = Column(String(14), primary_key=True)
    safemode_status = Column(Boolean, default=False)

    def __init__(self, chat_id: Union[int, str], safemode_status: bool = False):
        self.chat_id = str(chat_id)
        self.safemode_status = safemode_status

    def __repr__(self):
        return f"<Safemode chat_id={self.chat_id} status={self.safemode_status}>"


SAFEMODE_LOCK = threading.RLock()


def set_safemode(chat_id: Union[int, str], safemode_status: bool = True):
    with SAFEMODE_LOCK:
        chat_id = str(chat_id)
        curr = SESSION.query(Safemode).get(chat_id)
        if curr:
            curr.safemode_status = safemode_status
        else:
            curr = Safemode(chat_id, safemode_status)
            SESSION.add(curr)
        SESSION.commit()


def is_safemoded(chat_id: Union[int, str]) -> bool:
    try:
        record = SESSION.query(Safemode).get(str(chat_id))
        return record.safemode_status if record else False
    finally:
        SESSION.close()
