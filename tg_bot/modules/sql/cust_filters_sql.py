import threading
from sql import db

# MongoDB collections
filters_collection = db["cust_filters"]
buttons_collection = db["cust_buttons"]

CUST_FILT_LOCK = threading.RLock()
BUTTON_LOCK = threading.RLock()

CHAT_FILTERS = {}
BTN = {}

# ✅ Add a custom filter
def add_filter(chat_id, keyword, reply):
    with CUST_FILT_LOCK:
        filters_collection.update_one(
            {"chat_id": str(chat_id), "name": keyword},
            {"$set": {"keyword": reply}},
            upsert=True,
        )
        CHAT_FILTERS.setdefault(str(chat_id), {})[keyword] = reply

# ✅ Remove a custom filter
def remove_filter(chat_id, keyword):
    with CUST_FILT_LOCK:
        result = filters_collection.delete_one({"chat_id": str(chat_id), "name": keyword})
        if result.deleted_count:
            CHAT_FILTERS.get(str(chat_id), {}).pop(keyword, None)
            return True
        return False

# ✅ Get a specific filter
def get_filter(chat_id, keyword):
    return CHAT_FILTERS.get(str(chat_id), {}).get(keyword)

# ✅ Get all filters in a chat
def get_chat_filters(chat_id):
    return CHAT_FILTERS.get(str(chat_id), {})

# ✅ Add a button to a filter
def add_button(chat_id, keyword, name, url, same_line=True):
    with BUTTON_LOCK:
        buttons_collection.update_one(
            {"chat_id": str(chat_id), "keyword": keyword, "name": name},
            {"$set": {"url": url, "same_line": same_line}},
            upsert=True
        )
        BTN.setdefault(str(chat_id), {}).setdefault(keyword, []).append((name, url, same_line))

# ✅ Get buttons for a specific filter
def get_buttons(chat_id, keyword):
    return BTN.get(str(chat_id), {}).get(keyword, [])

# ✅ Delete all buttons for a specific keyword
def delete_button(chat_id, keyword):
    with BUTTON_LOCK:
        buttons_collection.delete_many({"chat_id": str(chat_id), "keyword": keyword})
        if str(chat_id) in BTN and keyword in BTN[str(chat_id)]:
            del BTN[str(chat_id)][keyword]

# ✅ Get all filters in DB
def get_all_filters():
    return list(filters_collection.find())

# ✅ Load filters and buttons into memory on startup
def __load_chat_filters():
    global CHAT_FILTERS, BTN

    all_filters = filters_collection.find()
    for filt in all_filters:
        CHAT_FILTERS.setdefault(filt["chat_id"], {})[filt["name"]] = filt["keyword"]

    all_btns = buttons_collection.find()
    for btn in all_btns:
        BTN.setdefault(btn["chat_id"], {}).setdefault(btn["keyword"], []).append(
            (btn["name"], btn["url"], btn.get("same_line", True))
        )

# ✅ Migrate filter and button data from old chat to new chat
def migrate_chat(old_chat_id, new_chat_id):
    old_id = str(old_chat_id)
    new_id = str(new_chat_id)

    with CUST_FILT_LOCK:
        filters = filters_collection.find({"chat_id": old_id})
        for filt in filters:
            filters_collection.update_one(
                {"chat_id": new_id, "name": filt["name"]},
                {"$set": {"keyword": filt["keyword"]}},
                upsert=True
            )
        filters_collection.delete_many({"chat_id": old_id})

        CHAT_FILTERS[new_id] = CHAT_FILTERS.get(old_id, {})
        if old_id in CHAT_FILTERS:
            del CHAT_FILTERS[old_id]

    with BUTTON_LOCK:
        buttons = buttons_collection.find({"chat_id": old_id})
        for btn in buttons:
            buttons_collection.update_one(
                {"chat_id": new_id, "keyword": btn["keyword"], "name": btn["name"]},
                {"$set": {
                    "url": btn["url"],
                    "same_line": btn.get("same_line", True)
                }},
                upsert=True
            )
        buttons_collection.delete_many({"chat_id": old_id})

        BTN[new_id] = BTN.get(old_id, {})
        if old_id in BTN:
            del BTN[old_id]

__load_chat_filters()
