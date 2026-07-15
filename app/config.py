import os

from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "receipt")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change_me")
POSTGRES_DB = os.getenv("POSTGRES_DB", "receipts")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
