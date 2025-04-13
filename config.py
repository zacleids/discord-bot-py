import os
from enum import Enum
from dotenv import load_dotenv

class Environment(Enum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"

class Config:
    def __init__(self):
        self.environment = Environment(os.getenv("ENV", "development").lower())
        
        # Load the appropriate .env file
        env_file = ".env.test" if self.environment == Environment.TESTING else ".env"
        load_dotenv(env_file)
        
        # Bot configuration
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.bot_admin_id = int(os.getenv('BOT_ADMIN_ID'))
        self.command_prefix = os.getenv('COMMAND_PREFIX', "!")
        
        # Database configuration
        db_prefix = "test" if self.environment == Environment.TESTING else "bot"
        self.db_name = f"{db_prefix}.db"
        self.db_orm_name = f"{db_prefix}_orm.db"
        self.db_path = os.path.join(os.path.dirname(__file__), "db", self.db_name)
        self.db_orm_path = os.path.join(os.path.dirname(__file__), "db", self.db_orm_name)
