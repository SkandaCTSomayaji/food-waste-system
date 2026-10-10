import os
from dotenv import load_dotenv

load_dotenv()

uri = os.environ.get("DATABASE_URL", "")

# Force the psycopg2 driver (SQLAlchemy 2.1 defaults to psycopg3)
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql+psycopg2://", 1)
elif uri.startswith("postgresql://"):
    uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # reject uploads over 5 MB