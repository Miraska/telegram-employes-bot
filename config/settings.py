import os
from dotenv import load_dotenv

load_dotenv()
class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    AIRTABLE_WEBHOOK: str = os.getenv("AIRTABLE_WEBHOOK")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "employees.db")
    ADMIN_USERNAMES: list = os.getenv("ADMIN_USERNAMES", "").split(",")

settings = Settings()