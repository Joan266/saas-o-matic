CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company     TEXT    NOT NULL,
    fiscal_id   TEXT    NOT NULL UNIQUE,
    email       TEXT    NOT NULL,
    country     TEXT    NOT NULL,
    plan        TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now')),
    updated_at  TEXT    DEFAULT (datetime('now'))
);

-- Keep updated_at current automatically on every UPDATE
CREATE TRIGGER IF NOT EXISTS customers_updated_at
AFTER UPDATE ON customers
FOR EACH ROW
BEGIN
    UPDATE customers SET updated_at = datetime('now') WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS simulations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   INTEGER NOT NULL REFERENCES customers(id),
    active_users  INTEGER NOT NULL CHECK (active_users >= 1),
    storage_gb    INTEGER NOT NULL CHECK (storage_gb >= 1),
    api_calls     INTEGER NOT NULL CHECK (api_calls >= 0),
    base_cost     REAL    NOT NULL,
    tax_rate      REAL    NOT NULL,
    total_cost    REAL    NOT NULL,
    created_at    TEXT    DEFAULT (datetime('now'))
);
