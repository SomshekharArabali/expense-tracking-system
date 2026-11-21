# Spec: Step 1 — Database Setup

## Requirements
1. **Database Technology**: SQLite 3
2. **Database Helpers in `database/db.py`**:
   - `get_db(db_path=None)`: Returns an open SQLite connection with:
     - `row_factory` set to `sqlite3.Row`
     - Foreign key enforcement enabled via `PRAGMA foreign_keys = ON;`
     - Reuses connection within Flask application context (`g.db`)
   - `close_db(e=None)`: Closes connection on application context teardown
   - `init_db(db_path=None)`: Creates tables using `CREATE TABLE IF NOT EXISTS`
   - `seed_db(db_path=None)`: Seeds default categories, sample demo user (`Nitish Kumar`, `nitish@example.com`), and sample expenses. Must be idempotent.
3. **Database Schema**:
   - `users`:
     - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
     - `name`: TEXT NOT NULL
     - `email`: TEXT UNIQUE NOT NULL
     - `password_hash`: TEXT NOT NULL
     - `monthly_budget`: REAL DEFAULT 0.0
     - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - `categories`:
     - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
     - `name`: TEXT UNIQUE NOT NULL
   - `expenses`:
     - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
     - `user_id`: INTEGER NOT NULL (FOREIGN KEY -> users.id ON DELETE CASCADE)
     - `category_id`: INTEGER (FOREIGN KEY -> categories.id ON DELETE SET NULL)
     - `amount`: REAL NOT NULL
     - `description`: TEXT
     - `date`: TEXT NOT NULL
     - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
4. **Flask CLI Commands**:
   - `flask init-db`: Initializes tables
   - `flask seed-db`: Seeds initial categories and demo data
