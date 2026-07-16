import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.config import DB_PATH as DB_PATH_ENV

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path(__file__).parent.parent / "saas_o_matic.db"
DB_PATH = Path(DB_PATH_ENV) if DB_PATH_ENV else _DEFAULT_DB_PATH

_SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def init_db() -> None:
    schema = _SCHEMA_PATH.read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(schema)
    logger.info("Database initialized at %s", DB_PATH)


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
