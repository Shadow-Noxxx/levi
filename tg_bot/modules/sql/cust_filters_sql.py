import threading
from sqlalchemy import Column, String, UnicodeText, Integer, Boolean
from tg_bot.modules.sql import BASE, SESSION


class CustomFilters(BASE):
    __tablename__ = "cust_filters"

    chat_id = Column(String(14), primary_key=True)
    name = Column(String(100), primary_key=True)
    keyword = Column(UnicodeText)

    def __init__(self, chat_id, name, keyword):
        self.chat_id = str(chat_id)
        self.name = name
        self.keyword = keyword


class Buttons(BASE):
    __tablename__ = "cust_buttons"

    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True)
    name = Column(String(32), primary_key=True)
    url = Column(UnicodeText)
    same_line = Column(Boolean, default=True)

    def __init__(self, chat_id, keyword, name, url, same_line=True):
        self.chat_id = str(chat_id)
        self.keyword = keyword
        self.name = name
        self.url = url
        self.same_line = same_line


CUST_FILT_LOCK = threading.RLock()
CHAT_FILTERS = {}

BUTTON_LOCK = threading.RLock()
BTN = {}


def add_filter(chat_id, keyword, reply):
    with CUST_FILT_LOCK:
        filt = CustomFilters(str(chat_id), keyword, reply)
        SESSION.merge(filt)
        SESSION.commit()
        CHAT_FILTERS.setdefault(str(chat_id), {})[keyword] = reply


def remove_filter(chat_id, keyword):
    with CUST_FILT_LOCK:
        filt = SESSION.query(CustomFilters).get((str(chat_id), keyword))
        if filt:
            if keyword in CHAT_FILTERS.get(str(chat_id), {}):
                del CHAT_FILTERS[str(chat_id)][keyword]
            SESSION.delete(filt)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def get_filter(chat_id, keyword):
    return CHAT_FILTERS.get(str(chat_id), {}).get(keyword)


def get_chat_filters(chat_id):
    return CHAT_FILTERS.get(str(chat_id), {})


def add_button(chat_id, keyword, name, url, same_line=True):
    with BUTTON_LOCK:
        btn = Buttons(str(chat_id), keyword, name, url, same_line)
        SESSION.merge(btn)
        SESSION.commit()
        BTN.setdefault(str(chat_id), {}).setdefault(keyword, []).append((name, url, same_line))


def get_buttons(chat_id, keyword):
    return BTN.get(str(chat_id), {}).get(keyword, [])


def delete_button(chat_id, keyword):
    with BUTTON_LOCK:
        btns = SESSION.query(Buttons).filter(Buttons.chat_id == str(chat_id), Buttons.keyword == keyword).all()
        for btn in btns:
            SESSION.delete(btn)
        SESSION.commit()
        if chat_id in BTN and keyword in BTN[chat_id]:
            del BTN[chat_id][keyword]


def get_all_filters():
    try:
        return SESSION.query(CustomFilters).all()
    finally:
        SESSION.close()


def __load_chat_filters():
    global CHAT_FILTERS, BTN
    try:
        all_filters = SESSION.query(CustomFilters).all()
        for filt in all_filters:
            CHAT_FILTERS.setdefault(filt.chat_id, {})[filt.name] = filt.keyword

        all_btns = SESSION.query(Buttons).all()
        for btn in all_btns:
            BTN.setdefault(btn.chat_id, {}).setdefault(btn.keyword, []).append((btn.name, btn.url, btn.same_line))
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with CUST_FILT_LOCK:
        chat_filters = SESSION.query(CustomFilters).filter(CustomFilters.chat_id == str(old_chat_id)).all()
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()
        CHAT_FILTERS[str(new_chat_id)] = CHAT_FILTERS[str(old_chat_id)]
        del CHAT_FILTERS[str(old_chat_id)]

        with BUTTON_LOCK:
            chat_buttons = SESSION.query(Buttons).filter(Buttons.chat_id == str(old_chat_id)).all()
            for btn in chat_buttons:
                btn.chat_id = str(new_chat_id)
            SESSION.commit()


__load_chat_filters()
