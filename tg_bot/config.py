from tg_bot.sample_config import Config

class Development(Config):
    OWNER_ID = 7819315360  # Your Telegram user ID
    OWNER_USERNAME = "@fos_founder"  # Your @username
    API_KEY = "7252339580:AAGz8jW4iqSrOM6NQ_ybIjckzaVqbMYCM1A"
    SQLALCHEMY_DATABASE_URI = 'postgresql://PostgreSQL 17:monarch@localhost:5432/mydb'
    MESSAGE_DUMP = '-1002620872464'  # Optional: a private group/channel ID to log deleted messages
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [8162803790, 7819315360]  # IDs of other trusted users
    LOAD = []  # List of modules to load (leave empty to load all)
    NO_LOAD = []  # Modules to skip
