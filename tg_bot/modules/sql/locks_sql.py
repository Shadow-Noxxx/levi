import threading
from sqlalchemy import Column, String, Boolean
from tg_bot.modules.sql import SESSION, BASE

class Permissions(BASE):
    __tablename__ = "permissions"
    chat_id = Column(String(14), primary_key=True)
    # Booleans mean "is locked"
    audio = Column(Boolean, default=False)
    voice = Column(Boolean, default=False)
    contact = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    videonote = Column(Boolean, default=False)
    document = Column(Boolean, default=False)
    photo = Column(Boolean, default=False)
    sticker = Column(Boolean, default=False)
    gif = Column(Boolean, default=False)
    url = Column(Boolean, default=False)
    bots = Column(Boolean, default=False)
    forward = Column(Boolean, default=False)
    game = Column(Boolean, default=False)
    location = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)


class Restrictions(BASE):
    __tablename__ = "restrictions"
    chat_id = Column(String(14), primary_key=True)
    messages = Column(Boolean, default=False)
    media = Column(Boolean, default=False)
    other = Column(Boolean, default=False)
    preview = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)


PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()


def init_permissions(chat_id, reset=False):
    curr = SESSION.query(Permissions).get(str(chat_id))
    if reset and curr:
        SESSION.delete(curr)
        SESSION.flush()
    new_perm = Permissions(chat_id)
    SESSION.add(new_perm)
    SESSION.commit()
    return new_perm


def init_restrictions(chat_id, reset=False):
    curr = SESSION.query(Restrictions).get(str(chat_id))
    if reset and curr:
        SESSION.delete(curr)
        SESSION.flush()
    new_restr = Restrictions(chat_id)
    SESSION.add(new_restr)
    SESSION.commit()
    return new_restr


def update_lock(chat_id, lock_type, locked):
    with PERM_LOCK:
        curr = SESSION.query(Permissions).get(str(chat_id))
        if not curr:
            curr = init_permissions(chat_id)
        setattr(curr, lock_type, locked)
        SESSION.commit()


def update_restriction(chat_id, restr_type, locked):
    with RESTR_LOCK:
        curr = SESSION.query(Restrictions).get(str(chat_id))
        if not curr:
            curr = init_restrictions(chat_id)

        if restr_type == "all":
            curr.messages = curr.media = curr.other = curr.preview = locked
        else:
            if restr_type == "previews":
                restr_type = "preview"
            setattr(curr, restr_type, locked)

        SESSION.commit()


def is_locked(chat_id, lock_type):
    curr = SESSION.query(Permissions).get(str(chat_id))
    result = getattr(curr, lock_type, False) if curr else False
    SESSION.close()
    return result


def is_restr_locked(chat_id, lock_type):
    curr = SESSION.query(Restrictions).get(str(chat_id))
    result = False
    if curr:
        if lock_type == "all":
            result = curr.messages and curr.media and curr.other and curr.preview
        elif lock_type == "previews":
            result = curr.preview
        else:
            result = getattr(curr, lock_type, False)
    SESSION.close()
    return result


def get_locks(chat_id):
    try:
        return SESSION.query(Permissions).get(str(chat_id))
    finally:
        SESSION.close()


def get_restr(chat_id):
    try:
        return SESSION.query(Restrictions).get(str(chat_id))
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with PERM_LOCK:
        perms = SESSION.query(Permissions).get(str(old_chat_id))
        if perms:
            perms.chat_id = str(new_chat_id)
        SESSION.commit()

    with RESTR_LOCK:
        rest = SESSION.query(Restrictions).get(str(old_chat_id))
        if rest:
            rest.chat_id = str(new_chat_id)
        SESSION.commit()
