import os

ALLOWED_ORIGINS: list[str] = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:4200,http://localhost:3000",
).split(",")

RATE_LIMIT: str = os.getenv("RATE_LIMIT", "60/minute")

DB_PATH: str = os.getenv("DB_PATH", "")  # empty = default path in database.py
