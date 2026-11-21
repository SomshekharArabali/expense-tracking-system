import os
import sqlite3
from flask import g, has_app_context, current_app
from werkzeug.security import generate_password_hash

# Default SQLite database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "spendly.db")


def get_db(db_path=None):
    """
    Returns a SQLite connection with row_factory set to sqlite3.Row
    and foreign keys enabled. Reuses connection in Flask app context when possible.
    """
    if db_path is None:
        if has_app_context():
            db_path = current_app.config.get("DATABASE", DEFAULT_DB_PATH)
        else:
            db_path = DEFAULT_DB_PATH

    # If within Flask application context and default/configured db_path is used
    if has_app_context() and (db_path == current_app.config.get("DATABASE", DEFAULT_DB_PATH)):
        if "db" not in g:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db

    # Standalone connection
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def close_db(e=None):
    """
    Closes the database connection if one was opened in the current Flask request context.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path=None):
    """
    Creates all required tables (users, categories, expenses) using CREATE TABLE IF NOT EXISTS.
    """
    conn = get_db(db_path)

    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        monthly_budget REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER,
        amount REAL NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
    );
    """
    conn.executescript(schema)
    conn.commit()

    if not has_app_context():
        conn.close()


def seed_db(db_path=None):
    """
    Seeds initial default categories and sample user/expense data for development.
    Operation is idempotent and safe to run multiple times.
    """
    # Ensure tables exist
    init_db(db_path)

    conn = get_db(db_path)

    # 1. Seed Categories (Idempotent)
    categories = [
        "Food",
        "Travel",
        "Bills",
        "Shopping",
        "Entertainment",
        "Health",
        "Other",
    ]
    for cat in categories:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    # 2. Seed Demo User (Idempotent)
    demo_email = "nitish@example.com"
    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?", (demo_email,)
    ).fetchone()

    if existing_user is None:
        hashed_pw = generate_password_hash("password123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, monthly_budget) VALUES (?, ?, ?, ?)",
            ("Nitish Kumar", demo_email, hashed_pw, 25000.0),
        )
        user_id = cursor.lastrowid
    else:
        user_id = existing_user["id"]

    # 3. Seed Sample Expenses (Idempotent)
    expense_count = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    if expense_count == 0:
        cat_map = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM categories").fetchall()
        }

        sample_expenses = [
            (user_id, cat_map.get("Food"), 5400.0, "Monthly grocery shopping", "2026-11-05"),
            (user_id, cat_map.get("Travel"), 3200.0, "Metro smart card recharge & cabs", "2026-11-08"),
            (user_id, cat_map.get("Bills"), 9640.0, "Electricity, water & broadband bills", "2026-11-12"),
        ]

        conn.executemany(
            """
            INSERT INTO expenses (user_id, category_id, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample_expenses,
        )

    conn.commit()

    if not has_app_context():
        conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded successfully.")
