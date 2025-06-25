import os
from enum import Enum

from dotenv import load_dotenv


class Environment(Enum):
    PROD = "PROD"
    DEV = "DEV"
    TEST = "TEST"


class Config:
    def __init__(self):
        self._log_buffer = []  # Buffer for early config log events
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
        self.discord_token = os.getenv("DISCORD_TOKEN")
        self.bot_admin_id = int(os.getenv("BOT_ADMIN_ID"))
        self.command_prefix = os.getenv("COMMAND_PREFIX", "!")

        # Database configuration
        self.db_name = f"{db_prefix}.db"
        self.db_orm_name = f"{db_prefix}_orm.db"
        # Always use the shared/db directory relative to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_dir = os.path.join(project_root, "shared", "db")
        os.makedirs(db_dir, exist_ok=True)

        self.db_path = os.path.join(db_dir, self.db_name)
        self.db_orm_path = os.path.join(db_dir, self.db_orm_name)

        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Configurations for various features

        self.performance_warning_threshold = self._load_performance_warning_threshold()

    def _buffer_log_event(self, event_type, context, level):
        self._log_buffer.append((event_type, context, level))

    def flush_log_buffer(self):
        try:
            from .log import log_event

            for event_type, context, level in self._log_buffer:
                log_event(event_type, context, level)
            self._log_buffer.clear()
        except Exception as e:
            print(f"Failed to flush log buffer: {e}")
            pass

    def _load_performance_warning_threshold(self):
        """Load the performance warning threshold from environment variable or default to 1.0."""
        try:
            val = float(os.environ.get("PERFORMANCE_WARNING_THRESHOLD", "1.0"))
            self._buffer_log_event(
                "CONFIG_LOADED", {"event": "CONFIG_LOADED", "message": "Loaded PERFORMANCE_WARNING_THRESHOLD", "value": val}, "DEBUG"
            )
            return val
        except Exception:
            self._buffer_log_event(
                "CONFIG_ERROR",
                {
                    "event": "CONFIG_ERROR",
                    "message": "Invalid PERFORMANCE_WARNING_THRESHOLD, defaulting to 1.0",
                    "value": os.environ.get("PERFORMANCE_WARNING_THRESHOLD"),
                },
                "WARNING",
            )
            return 1.0


# At the end of the file, create and export a single config instance
config = Config()
