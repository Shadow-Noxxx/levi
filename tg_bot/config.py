from tg_bot.sample_config import Config

class Development(Config):
    OWNER_ID = 7819315360  # Your Telegram user ID
    OWNER_USERNAME = "@fos_founder"  # Your @username
    API_KEY = "8013665655:AAFweEVPS0k5lXdv3Axn6KM-Hfub74rmkh8"
    SQLALCHEMY_DATABASE_URI = 'mongodb+srv://TEAMBABY01:UTTAMRATHORE09@cluster0.vmjl9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
    MESSAGE_DUMP = '-1002620872464'  # Optional: a private group/channel ID to log deleted messages
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [8162803790, 7819315360]  # IDs of other trusted users
    LOAD = []  # List of modules to load (leave empty to load all)
    NO_LOAD = []  # Modules to skip
