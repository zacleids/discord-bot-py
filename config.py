import os
from enum import Enum
from dotenv import load_dotenv

class Environment(Enum):
    PROD = "PROD"
    DEV = "DEV"
    TEST = "TEST"

class Config:
    def __init__(self):
        self.environment = Environment(os.getenv("ENV", "DEV"))
        
        # If running under pytest, override with .env.test
        if "PYTEST_CURRENT_TEST" in os.environ or os.getenv("ENV") == "TEST":
            load_dotenv(".env.test", override=True)
            os.environ["ENV"] = "TEST"
        else:
            load_dotenv(".env", override=True)
        self.environment = Environment(os.getenv("ENV", "DEV"))

        db_prefix = "bot"
        if self.environment == Environment.TEST:
            db_prefix = "test"

        # Bot configuration
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.bot_admin_id = int(os.getenv('BOT_ADMIN_ID'))
        self.command_prefix = os.getenv('COMMAND_PREFIX', "!")

        # Database configuration
        self.db_name = f"{db_prefix}.db"
        self.db_orm_name = f"{db_prefix}_orm.db"
        self.db_path = os.path.join(os.path.dirname(__file__), "db", self.db_name)
        self.db_orm_path = os.path.join(os.path.dirname(__file__), "db", self.db_orm_name)
