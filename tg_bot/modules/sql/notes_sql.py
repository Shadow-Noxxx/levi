import threading
from pymongo import ASCENDING
from tg_bot.modules.helper_funcs.msg_types import Types
from sql import db

notes_collection = db["notes"]
buttons_collection = db["note_buttons"]

NOTES_LOCK = threading.RLock()
BUTTONS_LOCK = threading.RLock()


def add_note_to_db(chat_id, note_name, note_data, msgtype, buttons=None, file=None):
    buttons = buttons or []
    chat_id = str(chat_id)

    with NOTES_LOCK:
        notes_collection.delete_one({"chat_id": chat_id, "name": note_name})
        buttons_collection.delete_many({"chat_id": chat_id, "note_name": note_name})

        notes_collection.insert_one({
            "chat_id": chat_id,
            "name": note_name,
            "value": note_data or "",
            "file": file,
            "msgtype": msgtype.value,
            "is_reply": False,
            "has_buttons": bool(buttons)
        })

    for b_name, url, same_line in buttons:
        add_note_button_to_db(chat_id, note_name, b_name, url, same_line)


def get_note(chat_id, note_name):
    return notes_collection.find_one({"chat_id": str(chat_id), "name": note_name})


def rm_note(chat_id, note_name):
    chat_id = str(chat_id)
    with NOTES_LOCK:
        note = notes_collection.find_one({"chat_id": chat_id, "name": note_name})
        if note:
            buttons_collection.delete_many({"chat_id": chat_id, "note_name": note_name})
            notes_collection.delete_one({"chat_id": chat_id, "name": note_name})
            return True
        return False


def get_all_chat_notes(chat_id):
    return list(notes_collection.find({"chat_id": str(chat_id)}).sort("name", ASCENDING))


def add_note_button_to_db(chat_id, note_name, b_name, url, same_line):
    with BUTTONS_LOCK:
        buttons_collection.insert_one({
            "chat_id": str(chat_id),
            "note_name": note_name,
            "name": b_name,
            "url": url,
            "same_line": same_line
        })


def get_buttons(chat_id, note_name):
    return list(buttons_collection.find(
        {"chat_id": str(chat_id), "note_name": note_name}
    ).sort("_id", ASCENDING))


def num_notes():
    return notes_collection.count_documents({})


def num_chats():
    return len(notes_collection.distinct("chat_id"))


def migrate_chat(old_chat_id, new_chat_id):
    old_chat_id = str(old_chat_id)
    new_chat_id = str(new_chat_id)

    with NOTES_LOCK:
        notes = list(notes_collection.find({"chat_id": old_chat_id}))
        for note in notes:
            note["chat_id"] = new_chat_id
            notes_collection.insert_one(note)
        notes_collection.delete_many({"chat_id": old_chat_id})

    with BUTTONS_LOCK:
        buttons = list(buttons_collection.find({"chat_id": old_chat_id}))
        for btn in buttons:
            btn["chat_id"] = new_chat_id
            buttons_collection.insert_one(btn)
        buttons_collection.delete_many({"chat_id": old_chat_id})
