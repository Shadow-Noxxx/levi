import threading
from typing import Optional

from sqlalchemy import Column, Integer, UnicodeText

from tg_bot.modules.sql import SESSION, BASE


class UserInfo(BASE):
    __tablename__ = "userinfo"

    user_id = Column(Integer, primary_key=True)
    info = Column(UnicodeText)

    def __init__(self, user_id: int, info: str):
        self.user_id = user_id
        self.info = info

    def __repr__(self):
        return f"<UserInfo user_id={self.user_id}>"


class UserBio(BASE):
    __tablename__ = "userbio"

    user_id = Column(Integer, primary_key=True)
    bio = Column(UnicodeText)

    def __init__(self, user_id: int, bio: str):
        self.user_id = user_id
        self.bio = bio

    def __repr__(self):
        return f"<UserBio user_id={self.user_id}>"


INSERTION_LOCK = threading.RLock()


def get_user_me_info(user_id: int) -> Optional[str]:
    try:
        userinfo = SESSION.query(UserInfo).get(user_id)
        return userinfo.info if userinfo else None
    finally:
        SESSION.close()


def set_user_me_info(user_id: int, info: str):
    with INSERTION_LOCK:
        record = SESSION.query(UserInfo).get(user_id)
        if record:
            record.info = info
        else:
            record = UserInfo(user_id, info)
            SESSION.add(record)
        SESSION.commit()


def get_user_bio(user_id: int) -> Optional[str]:
    try:
        userbio = SESSION.query(UserBio).get(user_id)
        return userbio.bio if userbio else None
    finally:
        SESSION.close()


def set_user_bio(user_id: int, bio: str):
    with INSERTION_LOCK:
        record = SESSION.query(UserBio).get(user_id)
        if record:
            record.bio = bio
        else:
            record = UserBio(user_id, bio)
            SESSION.add(record)
        SESSION.commit()


def clear_user_info(user_id: int) -> bool:
    with INSERTION_LOCK:
        record = SESSION.query(UserInfo).get(user_id)
        if record:
            SESSION.delete(record)
            SESSION.commit()
            return True
        return False


def clear_user_bio(user_id: int) -> bool:
    with INSERTION_LOCK:
        record = SESSION.query(UserBio).get(user_id)
        if record:
            SESSION.delete(record)
            SESSION.commit()
            return True
        return False
