import threading
from typing import Union

from sqlalchemy import Column, Integer, String, Boolean

from tg_bot.modules.sql import SESSION, BASE


class ReportingUserSettings(BASE):
    __tablename__ = "user_report_settings"

    user_id = Column(Integer, primary_key=True)
    should_report = Column(Boolean, default=True)

    def __init__(self, user_id: int):
        self.user_id = user_id

    def __repr__(self):
        return f"<UserReportSettings {self.user_id}>"


class ReportingChatSettings(BASE):
    __tablename__ = "chat_report_settings"

    chat_id = Column(String(14), primary_key=True)
    should_report = Column(Boolean, default=True)

    def __init__(self, chat_id: Union[str, int]):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return f"<ChatReportSettings {self.chat_id}>"


CHAT_LOCK = threading.RLock()
USER_LOCK = threading.RLock()


def chat_should_report(chat_id: Union[int, str]) -> bool:
    try:
        setting = SESSION.query(ReportingChatSettings).get(str(chat_id))
        return setting.should_report if setting else False
    finally:
        SESSION.close()


def user_should_report(user_id: int) -> bool:
    try:
        setting = SESSION.query(ReportingUserSettings).get(user_id)
        return setting.should_report if setting else True
    finally:
        SESSION.close()


def set_chat_setting(chat_id: Union[int, str], setting: bool):
    with CHAT_LOCK:
        chat_id = str(chat_id)
        record = SESSION.query(ReportingChatSettings).get(chat_id)

        if not record:
            record = ReportingChatSettings(chat_id)

        record.should_report = setting
        SESSION.add(record)
        SESSION.commit()


def set_user_setting(user_id: int, setting: bool):
    with USER_LOCK:
        record = SESSION.query(ReportingUserSettings).get(user_id)

        if not record:
            record = ReportingUserSettings(user_id)

        record.should_report = setting
        SESSION.add(record)
        SESSION.commit()


def migrate_chat(old_chat_id: Union[int, str], new_chat_id: Union[int, str]):
    with CHAT_LOCK:
        old_id, new_id = str(old_chat_id), str(new_chat_id)
        record = SESSION.query(ReportingChatSettings).get(old_id)

        if record:
            # Delete existing new_chat_id if exists to prevent PK conflict
            SESSION.query(ReportingChatSettings).filter_by(chat_id=new_id).delete()

            record.chat_id = new_id
            SESSION.commit()
