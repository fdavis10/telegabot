import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # По умолчанию admin123
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "your_admin_username")