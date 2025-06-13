import threading

from sqlalchemy import Column, String, Boolean, UnicodeText, Integer, BigInteger
from tg_bot.modules.helper_funcs.msg_types import Types
from tg_bot.modules.sql import SESSION, BASE

DEFAULT_WELCOME = "Hey {first}, how are you?"
DEFAULT_GOODBYE = "Nice knowing ya!"


class Welcome(BASE):
    __tablename__ = "welcome_pref"

    chat_id = Column(String(14), primary_key=True)
    should_welcome = Column(Boolean, default=True)
    should_goodbye = Column(Boolean, default=True)

    custom_welcome = Column(UnicodeText, default=DEFAULT_WELCOME)
    welcome_type = Column(Integer, default=Types.TEXT.value)

    custom_leave = Column(UnicodeText, default=DEFAULT_GOODBYE)
    leave_type = Column(Integer, default=Types.TEXT.value)

    clean_welcome = Column(BigInteger)
    del_joined = Column(BigInteger)

    def __init__(self, chat_id, should_welcome=True, should_goodbye=True):
        self.chat_id = str(chat_id)
        self.should_welcome = should_welcome
        self.should_goodbye = should_goodbye

    def __repr__(self):
        return f"<Chat {self.chat_id} should Welcome: {self.should_welcome}>"


class WelcomeButtons(BASE):
    __tablename__ = "welcome_urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.name = name
        self.url = url
        self.same_line = same_line


class GoodbyeButtons(BASE):
    __tablename__ = "leave_urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.name = name
        self.url = url
        self.same_line = same_line


# Create tables if not exist
Welcome.__table__.create(checkfirst=True)
WelcomeButtons.__table__.create(checkfirst=True)
GoodbyeButtons.__table__.create(checkfirst=True)

# Locks
INSERTION_LOCK = threading.RLock()
WELC_BTN_LOCK = threading.RLock()
LEAVE_BTN_LOCK = threading.RLock()


# --- Preference Getters/Setters ---

def get_welc_pref(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    if welc:
        return welc.should_welcome, welc.custom_welcome, welc.welcome_type
    return True, DEFAULT_WELCOME, Types.TEXT


def get_gdbye_pref(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    if welc:
        return welc.should_goodbye, welc.custom_leave, welc.leave_type
    return True, DEFAULT_GOODBYE, Types.TEXT


def set_clean_welcome(chat_id, clean_welcome):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id)) or Welcome(str(chat_id))
        curr.clean_welcome = int(clean_welcome)
        SESSION.add(curr)
        SESSION.commit()


def get_clean_pref(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    return welc.clean_welcome if welc else False


def set_del_joined(chat_id, del_joined):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id)) or Welcome(str(chat_id))
        curr.del_joined = int(del_joined)
        SESSION.add(curr)
        SESSION.commit()


def get_del_pref(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    return welc.del_joined if welc else False


def set_welc_preference(chat_id, should_welcome):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id)) or Welcome(str(chat_id), should_welcome=should_welcome)
        curr.should_welcome = should_welcome
        SESSION.add(curr)
        SESSION.commit()


def set_gdbye_preference(chat_id, should_goodbye):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id)) or Welcome(str(chat_id), should_goodbye=should_goodbye)
        curr.should_goodbye = should_goodbye
        SESSION.add(curr)
        SESSION.commit()


# --- Custom Messages & Buttons ---

def set_custom_welcome(chat_id, custom_welcome, welcome_type, buttons=None):
    buttons = buttons or []
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id)) or Welcome(str(chat_id))
        welcome_settings.custom_welcome = custom_welcome or DEFAULT_WELCOME
        welcome_settings.welcome_type = welcome_type.value
        SESSION.add(welcome_settings)

        with WELC_BTN_LOCK:
            SESSION.query(WelcomeButtons).filter_by(chat_id=str(chat_id)).delete()
            for name, url, same_line in buttons:
                SESSION.add(WelcomeButtons(chat_id, name, url, same_line))

        SESSION.commit()


def get_custom_welcome(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    return welc.custom_welcome if welc and welc.custom_welcome else DEFAULT_WELCOME


def set_custom_gdbye(chat_id, custom_goodbye, goodbye_type, buttons=None):
    buttons = buttons or []
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id)) or Welcome(str(chat_id))
        welcome_settings.custom_leave = custom_goodbye or DEFAULT_GOODBYE
        welcome_settings.leave_type = goodbye_type.value
        SESSION.add(welcome_settings)

        with LEAVE_BTN_LOCK:
            SESSION.query(GoodbyeButtons).filter_by(chat_id=str(chat_id)).delete()
            for name, url, same_line in buttons:
                SESSION.add(GoodbyeButtons(chat_id, name, url, same_line))

        SESSION.commit()


def get_custom_gdbye(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    return welc.custom_leave if welc and welc.custom_leave else DEFAULT_GOODBYE


def get_welc_buttons(chat_id):
    try:
        return SESSION.query(WelcomeButtons).filter_by(chat_id=str(chat_id)).order_by(WelcomeButtons.id).all()
    finally:
        SESSION.close()


def get_gdbye_buttons(chat_id):
    try:
        return SESSION.query(GoodbyeButtons).filter_by(chat_id=str(chat_id)).order_by(GoodbyeButtons.id).all()
    finally:
        SESSION.close()


# --- Chat Migration ---

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Welcome).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)

        with WELC_BTN_LOCK:
            buttons = SESSION.query(WelcomeButtons).filter_by(chat_id=str(old_chat_id)).all()
            for btn in buttons:
                btn.chat_id = str(new_chat_id)

        with LEAVE_BTN_LOCK:
            buttons = SESSION.query(GoodbyeButtons).filter_by(chat_id=str(old_chat_id)).all()
            for btn in buttons:
                btn.chat_id = str(new_chat_id)

        SESSION.commit()
