import threading
from typing import Optional, Tuple, List

from sqlalchemy import Integer, Column, String, UnicodeText, func, distinct, Boolean
from sqlalchemy.dialects import postgresql

from tg_bot.modules.sql import SESSION, BASE


class Warns(BASE):
    __tablename__ = "warns"

    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14), primary_key=True)
    num_warns = Column(Integer, default=0)
    reasons = Column(postgresql.ARRAY(UnicodeText))

    def __init__(self, user_id: int, chat_id: str):
        self.user_id = user_id
        self.chat_id = str(chat_id)
        self.num_warns = 0
        self.reasons = []

    def __repr__(self):
        return f"<{self.num_warns} warns for {self.user_id} in {self.chat_id} for reasons {self.reasons}>"


class WarnFilters(BASE):
    __tablename__ = "warn_filters"

    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id: str, keyword: str, reply: str):
        self.chat_id = str(chat_id)
        self.keyword = keyword
        self.reply = reply

    def __repr__(self):
        return f"<WarnFilter {self.keyword} for chat {self.chat_id}>"

    def __eq__(self, other):
        return isinstance(other, WarnFilters) and self.chat_id == other.chat_id and self.keyword == other.keyword


class WarnSettings(BASE):
    __tablename__ = "warn_settings"

    chat_id = Column(String(14), primary_key=True)
    warn_limit = Column(Integer, default=3)
    soft_warn = Column(Boolean, default=False)

    def __init__(self, chat_id: str, warn_limit: int = 3, soft_warn: bool = False):
        self.chat_id = str(chat_id)
        self.warn_limit = warn_limit
        self.soft_warn = soft_warn

    def __repr__(self):
        return f"<{self.chat_id} has warn limit {self.warn_limit}>"


# Locks
WARN_INSERTION_LOCK = threading.RLock()
WARN_FILTER_INSERTION_LOCK = threading.RLock()
WARN_SETTINGS_LOCK = threading.RLock()

# Cache for fast access
WARN_FILTERS: dict[str, List[str]] = {}


# Warn Management
def warn_user(user_id: int, chat_id: str, reason: Optional[str] = None) -> Tuple[int, List[str]]:
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id))) or Warns(user_id, chat_id)
        warned_user.num_warns += 1
        if reason:
            warned_user.reasons = (warned_user.reasons or []) + [reason]

        SESSION.add(warned_user)
        SESSION.commit()
        return warned_user.num_warns, warned_user.reasons


def remove_warn(user_id: int, chat_id: str) -> bool:
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if warned_user and warned_user.num_warns > 0:
            warned_user.num_warns -= 1
            SESSION.add(warned_user)
            SESSION.commit()
            return True
        return False


def reset_warns(user_id: int, chat_id: str):
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if warned_user:
            warned_user.num_warns = 0
            warned_user.reasons = []
            SESSION.add(warned_user)
            SESSION.commit()


def get_warns(user_id: int, chat_id: str) -> Optional[Tuple[int, List[str]]]:
    try:
        user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if not user:
            return None
        return user.num_warns, user.reasons
    finally:
        SESSION.close()


# Warn Filters
def add_warn_filter(chat_id: str, keyword: str, reply: str):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = WarnFilters(chat_id, keyword, reply)
        if keyword not in WARN_FILTERS.get(chat_id, []):
            WARN_FILTERS.setdefault(chat_id, []).append(keyword)
            WARN_FILTERS[chat_id] = sorted(WARN_FILTERS[chat_id], key=lambda x: (-len(x), x))

        SESSION.merge(warn_filt)
        SESSION.commit()


def remove_warn_filter(chat_id: str, keyword: str) -> bool:
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = SESSION.query(WarnFilters).get((chat_id, keyword))
        if warn_filt:
            if keyword in WARN_FILTERS.get(chat_id, []):
                WARN_FILTERS[chat_id].remove(keyword)
            SESSION.delete(warn_filt)
            SESSION.commit()
            return True
        return False


def get_chat_warn_triggers(chat_id: str) -> List[str]:
    return WARN_FILTERS.get(chat_id, [])


def get_chat_warn_filters(chat_id: str) -> List[WarnFilters]:
    try:
        return SESSION.query(WarnFilters).filter_by(chat_id=chat_id).all()
    finally:
        SESSION.close()


def get_warn_filter(chat_id: str, keyword: str) -> Optional[WarnFilters]:
    try:
        return SESSION.query(WarnFilters).get((chat_id, keyword))
    finally:
        SESSION.close()


# Settings
def set_warn_limit(chat_id: str, warn_limit: int):
    with WARN_SETTINGS_LOCK:
        setting = SESSION.query(WarnSettings).get(chat_id) or WarnSettings(chat_id, warn_limit=warn_limit)
        setting.warn_limit = warn_limit
        SESSION.add(setting)
        SESSION.commit()


def set_warn_strength(chat_id: str, soft_warn: bool):
    with WARN_SETTINGS_LOCK:
        setting = SESSION.query(WarnSettings).get(chat_id) or WarnSettings(chat_id, soft_warn=soft_warn)
        setting.soft_warn = soft_warn
        SESSION.add(setting)
        SESSION.commit()


def get_warn_setting(chat_id: str) -> Tuple[int, bool]:
    try:
        setting = SESSION.query(WarnSettings).get(chat_id)
        return (setting.warn_limit, setting.soft_warn) if setting else (3, False)
    finally:
        SESSION.close()


# Stats
def num_warns() -> int:
    try:
        return SESSION.query(func.sum(Warns.num_warns)).scalar() or 0
    finally:
        SESSION.close()


def num_warn_chats() -> int:
    try:
        return SESSION.query(func.count(distinct(Warns.chat_id))).scalar()
    finally:
        SESSION.close()


def num_warn_filters() -> int:
    try:
        return SESSION.query(WarnFilters).count()
    finally:
        SESSION.close()


def num_warn_chat_filters(chat_id: str) -> int:
    try:
        return SESSION.query(WarnFilters).filter_by(chat_id=chat_id).count()
    finally:
        SESSION.close()


def num_warn_filter_chats() -> int:
    try:
        return SESSION.query(func.count(distinct(WarnFilters.chat_id))).scalar()
    finally:
        SESSION.close()


# Migrations
def migrate_chat(old_chat_id: str, new_chat_id: str):
    with WARN_INSERTION_LOCK:
        for warn in SESSION.query(Warns).filter_by(chat_id=old_chat_id).all():
            warn.chat_id = new_chat_id
        SESSION.commit()

    with WARN_FILTER_INSERTION_LOCK:
        for filt in SESSION.query(WarnFilters).filter_by(chat_id=old_chat_id).all():
            filt.chat_id = new_chat_id
        SESSION.commit()
        if old_chat_id in WARN_FILTERS:
            WARN_FILTERS[new_chat_id] = WARN_FILTERS.pop(old_chat_id)

    with WARN_SETTINGS_LOCK:
        for setting in SESSION.query(WarnSettings).filter_by(chat_id=old_chat_id).all():
            setting.chat_id = new_chat_id
        SESSION.commit()


# Initial Load
def __load_chat_warn_filters():
    global WARN_FILTERS
    try:
        chats = SESSION.query(WarnFilters.chat_id).distinct().all()
        for (chat_id,) in chats:
            WARN_FILTERS[chat_id] = []

        for filt in SESSION.query(WarnFilters).all():
            WARN_FILTERS[filt.chat_id].append(filt.keyword)

        for cid in WARN_FILTERS:
            WARN_FILTERS[cid] = sorted(set(WARN_FILTERS[cid]), key=lambda i: (-len(i), i))
    finally:
        SESSION.close()


__load_chat_warn_filters()
