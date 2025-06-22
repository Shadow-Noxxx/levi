import threading
from typing import Optional

from pymongo import UpdateOne

from sql import db
from tg_bot.modules.helper_funcs.msg_types import Types

DEFAULT_WELCOME = "Hey {first}, how are you?"
DEFAULT_GOODBYE = "Nice knowing ya!"

welcome_col = db["welcome_pref"]
welc_btn_col = db["welcome_urls"]
leave_btn_col = db["leave_urls"]

# Locks
INSERTION_LOCK = threading.RLock()
WELC_BTN_LOCK = threading.RLock()
LEAVE_BTN_LOCK = threading.RLock()


# --- Preference Getters/Setters ---

def get_welc_pref(chat_id):
    pref = welcome_col.find_one({"chat_id": str(chat_id)})
    if pref:
        return pref.get("should_welcome", True), pref.get("custom_welcome", DEFAULT_WELCOME), Types(pref.get("welcome_type", Types.TEXT.value))
    return True, DEFAULT_WELCOME, Types.TEXT


def get_gdbye_pref(chat_id):
    pref = welcome_col.find_one({"chat_id": str(chat_id)})
    if pref:
        return pref.get("should_goodbye", True), pref.get("custom_leave", DEFAULT_GOODBYE), Types(pref.get("leave_type", Types.TEXT.value))
    return True, DEFAULT_GOODBYE, Types.TEXT


def set_clean_welcome(chat_id, clean_welcome):
    with INSERTION_LOCK:
        welcome_col.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"clean_welcome": int(clean_welcome)}},
            upsert=True
        )


def get_clean_pref(chat_id):
    pref = welcome_col.find_one({"chat_id": str(chat_id)})
    return pref.get("clean_welcome") if pref else False


def set_del_joined(chat_id, del_joined):
    with INSERTION_LOCK:
        welcome_col.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"del_joined": int(del_joined)}},
            upsert=True
        )


def get_del_pref(chat_id):
    pref = welcome_col.find_one({"chat_id": str(chat_id)})
    return pref.get("del_joined") if pref else False


def set_welc_preference(chat_id, should_welcome):
    with INSERTION_LOCK:
        welcome_col.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"should_welcome": should_welcome}},
            upsert=True
        )


def set_gdbye_preference(chat_id, should_goodbye):
    with INSERTION_LOCK:
        welcome_col.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"should_goodbye": should_goodbye}},
            upsert=True
        )


# --- Custom Messages & Buttons ---

def set_custom_welcome(chat_id, custom_welcome, welcome_type, buttons=None):
    buttons = buttons or []
    with INSERTION_LOCK:
        welcome_col.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"custom_welcome": custom_welcome or DEFAULT_WELCOME, "welcome_type": welcome_type.value}},
            upsert=True
        )
        with WELC_BTN_LOCK:
            welc_btn_col.delete_many({"chat_id": str(chat_id)})
            if buttons:
                welc_btn_col.insert_many([
                    {
                        "chat_id": str(chat_id),
                        "name": name,
                        "url": url,
                        "same_line": same_line
                    } for name, url, same_line in buttons
                ])


def get_custom_welcome(chat_id):
    pref = welcome_col.find_one({"chat_id": str(chat_id)})
    return pref.get("custom_welcome", DEFAULT_WELCOME) if pref else DEFAULT_WELCOME


def set_custom_gdbye(chat_id, custom_goodbye, goodbye_type, buttons=None):
    buttons = buttons or []
    with INSERTION_LOCK:
        welcome_col.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"custom_leave": custom_goodbye or DEFAULT_GOODBYE, "leave_type": goodbye_type.value}},
            upsert=True
        )
        with LEAVE_BTN_LOCK:
            leave_btn_col.delete_many({"chat_id": str(chat_id)})
            if buttons:
                leave_btn_col.insert_many([
                    {
                        "chat_id": str(chat_id),
                        "name": name,
                        "url": url,
                        "same_line": same_line
                    } for name, url, same_line in buttons
                ])


def get_custom_gdbye(chat_id):
    pref = welcome_col.find_one({"chat_id": str(chat_id)})
    return pref.get("custom_leave", DEFAULT_GOODBYE) if pref else DEFAULT_GOODBYE


def get_welc_buttons(chat_id):
    return list(welc_btn_col.find({"chat_id": str(chat_id)}))


def get_gdbye_buttons(chat_id):
    return list(leave_btn_col.find({"chat_id": str(chat_id)}))


# --- Chat Migration ---

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        doc = welcome_col.find_one({"chat_id": str(old_chat_id)})
        if doc:
            doc["chat_id"] = str(new_chat_id)
            welcome_col.replace_one({"chat_id": str(old_chat_id)}, doc, upsert=True)

        with WELC_BTN_LOCK:
            btns = list(welc_btn_col.find({"chat_id": str(old_chat_id)}))
            if btns:
                welc_btn_col.delete_many({"chat_id": str(old_chat_id)})
                welc_btn_col.insert_many([{**b, "chat_id": str(new_chat_id)} for b in btns])

        with LEAVE_BTN_LOCK:
            btns = list(leave_btn_col.find({"chat_id": str(old_chat_id)}))
            if btns:
                leave_btn_col.delete_many({"chat_id": str(old_chat_id)})
                leave_btn_col.insert_many([{**b, "chat_id": str(new_chat_id)} for b in btns])
