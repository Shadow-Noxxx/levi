import threading
from typing import Optional, List

from sqlalchemy import Column, Integer, UnicodeText, String, ForeignKey, UniqueConstraint, func

from tg_bot import dispatcher
from tg_bot.modules.sql import BASE, SESSION


class Users(BASE):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(UnicodeText)

    def __init__(self, user_id: int, username: Optional[str] = None):
        self.user_id = user_id
        self.username = username

    def __repr__(self):
        return f"<User {self.username} ({self.user_id})>"


class Chats(BASE):
    __tablename__ = "chats"
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id: str, chat_name: str):
        self.chat_id = str(chat_id)
        self.chat_name = chat_name

    def __repr__(self):
        return f"<Chat {self.chat_name} ({self.chat_id})>"


class ChatMembers(BASE):
    __tablename__ = "chat_members"
    priv_chat_id = Column(Integer, primary_key=True)
    chat = Column(String(14), ForeignKey("chats.chat_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = Column(Integer, ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint('chat', 'user', name='_chat_members_uc'),)

    def __init__(self, chat: str, user: int):
        self.chat = str(chat)
        self.user = user

    def __repr__(self):
        return f"<ChatMember user={self.user} chat={self.chat}>"


INSERTION_LOCK = threading.RLock()


def ensure_bot_in_db():
    with INSERTION_LOCK:
        bot = Users(dispatcher.bot.id, dispatcher.bot.username)
        SESSION.merge(bot)
        SESSION.commit()


def update_user(user_id: int, username: Optional[str], chat_id: Optional[str] = None, chat_name: Optional[str] = None):
    with INSERTION_LOCK:
        user = SESSION.query(Users).get(user_id)
        if not user:
            user = Users(user_id, username)
            SESSION.add(user)
        else:
            user.username = username

        if chat_id and chat_name:
            chat = SESSION.query(Chats).get(str(chat_id))
            if not chat:
                chat = Chats(str(chat_id), chat_name)
                SESSION.add(chat)
            else:
                chat.chat_name = chat_name

            member = SESSION.query(ChatMembers).filter_by(chat=str(chat_id), user=user_id).first()
            if not member:
                SESSION.add(ChatMembers(str(chat_id), user_id))

        SESSION.commit()


def get_userid_by_name(username: str) -> List[Users]:
    try:
        return SESSION.query(Users).filter(func.lower(Users.username) == username.lower()).all()
    finally:
        SESSION.close()


def get_name_by_userid(user_id: int) -> Optional[Users]:
    try:
        return SESSION.query(Users).filter_by(user_id=user_id).first()
    finally:
        SESSION.close()


def get_chat_members(chat_id: str) -> List[ChatMembers]:
    try:
        return SESSION.query(ChatMembers).filter_by(chat=str(chat_id)).all()
    finally:
        SESSION.close()


def get_all_chats() -> List[Chats]:
    try:
        return SESSION.query(Chats).all()
    finally:
        SESSION.close()


def get_user_num_chats(user_id: int) -> int:
    try:
        return SESSION.query(ChatMembers).filter_by(user=user_id).count()
    finally:
        SESSION.close()


def num_chats() -> int:
    try:
        return SESSION.query(Chats).count()
    finally:
        SESSION.close()


def num_users() -> int:
    try:
        return SESSION.query(Users).count()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id: str, new_chat_id: str):
    with INSERTION_LOCK:
        chat = SESSION.query(Chats).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)

        members = SESSION.query(ChatMembers).filter_by(chat=str(old_chat_id)).all()
        for member in members:
            member.chat = str(new_chat_id)
            SESSION.add(member)

        SESSION.commit()


def del_user(user_id: int) -> bool:
    with INSERTION_LOCK:
        members = SESSION.query(ChatMembers).filter_by(user=user_id).all()
        for member in members:
            SESSION.delete(member)

        user = SESSION.query(Users).get(user_id)
        if user:
            SESSION.delete(user)
            SESSION.commit()
            return True

        SESSION.commit()
    return False
