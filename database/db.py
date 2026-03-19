"""
database/db.py
SQLite backend — CC Crafts Sales Inventory System.
Tables: users, products (+ image_data BLOB, description), transactions
"""

import sqlite3
import hashlib
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


def _con() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ── Schema + live migration ────────────────────────────────────────────────────
def init() -> None:
    with _con() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT    NOT NULL UNIQUE,
                password   TEXT    NOT NULL,
                role       TEXT    NOT NULL DEFAULT 'staff',
                created_at TEXT    DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS products (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                emoji      TEXT    NOT NULL DEFAULT '🌸',
                name       TEXT    NOT NULL,
                category   TEXT    NOT NULL DEFAULT '',
                price      REAL    NOT NULL DEFAULT 0.0,
                stock      INTEGER NOT NULL DEFAULT 0,
                created_at TEXT    DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id   INTEGER NOT NULL,
                product_name TEXT    NOT NULL,
                qty_sold     INTEGER NOT NULL,
                unit_price   REAL    NOT NULL,
                total        REAL    NOT NULL,
                customer     TEXT    DEFAULT '',
                sold_at      TEXT    DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        """)
        # Live migrations — add new columns to existing DBs without data loss
        existing = [r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()]
        if "image_data" not in existing:
            conn.execute("ALTER TABLE products ADD COLUMN image_data BLOB DEFAULT NULL")
        if "description" not in existing:
            conn.execute("ALTER TABLE products ADD COLUMN description TEXT DEFAULT ''")
    _seed()


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _seed() -> None:
    with _con() as conn:
        if not conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            conn.executemany(
                "INSERT INTO users (username, password, role) VALUES (?,?,?)",
                [("admin", _hash("admin123"), "admin"),
                 ("staff", _hash("staff123"), "staff")],
            )
        if not conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
            conn.executemany(
                "INSERT INTO products (emoji,name,category,price,stock,description)"
                " VALUES (?,?,?,?,?,?)",
                [
                    ("🌹", "Rose Crochet Bouquet",  "Crochet Flowers",
                     350.0, 8, "Handcrafted crochet roses bundled into a timeless bouquet."),
                    ("🌻", "Sunflower Arrangement", "Fresh Flower Arrangement",
                     480.0, 3, "Bright sunflowers expertly arranged for any occasion."),
                    ("💐", "Mixed Crochet Bouquet", "Mixed Bouquet",
                     420.0, 12, "A colorful mix of crochet blooms in every hue."),
                    ("🎀", "Lavender Gift Set",      "Gift Set",
                     650.0, 0, "Elegant lavender gift set — perfect for gifting."),
                ],
            )


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════
def login(username: str, password: str) -> dict | None:
    with _con() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username.strip(), _hash(password)),
        ).fetchone()
    return dict(row) if row else None


def get_users() -> list[tuple]:
    with _con() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY username"
        ).fetchall()
    return [tuple(r) for r in rows]


def add_user(username: str, password: str, role: str = "staff") -> None:
    with _con() as conn:
        conn.execute(
            "INSERT INTO users (username,password,role) VALUES (?,?,?)",
            (username.strip(), _hash(password), role),
        )


def update_user_password(uid: int, new_password: str) -> None:
    with _con() as conn:
        conn.execute("UPDATE users SET password=? WHERE id=?", (_hash(new_password), uid))


def delete_user(uid: int) -> None:
    with _con() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (uid,))


# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCTS
#
#  Tuple layout (9 fields):
#    [0] id          [1] emoji      [2] name        [3] category
#    [4] price       [5] stock      [6] created_at
#    [7] image_data  (bytes | None)
#    [8] description (str)
# ══════════════════════════════════════════════════════════════════════════════
_SEL = ("SELECT id,emoji,name,category,price,stock,created_at,"
        "image_data,description FROM products")


def get_products(search: str = "") -> list[tuple]:
    with _con() as conn:
        if search:
            rows = conn.execute(
                _SEL + " WHERE name LIKE ? OR category LIKE ? ORDER BY name",
                (f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute(_SEL + " ORDER BY name").fetchall()
    return [tuple(r) for r in rows]


def get_available() -> list[tuple]:
    with _con() as conn:
        rows = conn.execute(_SEL + " WHERE stock > 0 ORDER BY name").fetchall()
    return [tuple(r) for r in rows]


def get_product(pid: int) -> tuple | None:
    with _con() as conn:
        row = conn.execute(_SEL + " WHERE id=?", (pid,)).fetchone()
    return tuple(row) if row else None


def add_product(
    emoji: str, name: str, category: str, price: float, stock: int,
    image_data: bytes | None = None, description: str = "",
) -> None:
    with _con() as conn:
        conn.execute(
            "INSERT INTO products (emoji,name,category,price,stock,image_data,description)"
            " VALUES (?,?,?,?,?,?,?)",
            (emoji, name, category, price, stock, image_data, description),
        )


def update_product(
    pid: int, emoji: str, name: str, category: str, price: float, stock: int,
    image_data: bytes | None = None, description: str = "",
    update_image: bool = True,
) -> None:
    with _con() as conn:
        if update_image:
            conn.execute(
                "UPDATE products SET emoji=?,name=?,category=?,price=?,stock=?,"
                "image_data=?,description=? WHERE id=?",
                (emoji, name, category, price, stock, image_data, description, pid),
            )
        else:
            conn.execute(
                "UPDATE products SET emoji=?,name=?,category=?,price=?,stock=?,"
                "description=? WHERE id=?",
                (emoji, name, category, price, stock, description, pid),
            )


def delete_product(pid: int) -> None:
    with _con() as conn:
        conn.execute("DELETE FROM transactions WHERE product_id=?", (pid,))
        conn.execute("DELETE FROM products WHERE id=?", (pid,))

# ══════════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════
def get_transactions(search: str = "") -> list[tuple]:
    with _con() as conn:
        if search:
            rows = conn.execute(
                "SELECT * FROM transactions"
                " WHERE product_name LIKE ? OR customer LIKE ?"
                " ORDER BY sold_at DESC",
                (f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY sold_at DESC"
            ).fetchall()
    return [tuple(r) for r in rows]


def record_sale(product_id: int, qty: int, customer: str = "") -> float:
    p = get_product(product_id)
    if not p:
        raise ValueError("Product not found.")
    if p[5] < qty:
        raise ValueError(f"Only {p[5]} units in stock.")
    total = float(p[4]) * qty
    with _con() as conn:
        conn.execute(
            "INSERT INTO transactions"
            " (product_id,product_name,qty_sold,unit_price,total,customer)"
            " VALUES (?,?,?,?,?,?)",
            (product_id, p[2], qty, p[4], total, customer),
        )
        conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id=?", (qty, product_id)
        )
    return total


# ══════════════════════════════════════════════════════════════════════════════
#  STATISTICS
# ══════════════════════════════════════════════════════════════════════════════
def stats() -> dict:
    with _con() as conn:
        products     = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        transactions = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        revenue      = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM transactions"
        ).fetchone()[0]
        low = conn.execute(
            "SELECT COUNT(*) FROM products WHERE stock > 0 AND stock <= 5"
        ).fetchone()[0]
        out = conn.execute(
            "SELECT COUNT(*) FROM products WHERE stock = 0"
        ).fetchone()[0]
    return dict(products=products, transactions=transactions,
                revenue=revenue, low=low, out=out)
