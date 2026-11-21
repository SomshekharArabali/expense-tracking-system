import os
import sqlite3
import pytest
from werkzeug.security import check_password_hash
from app import app
from database.db import get_db, init_db, seed_db, close_db


@pytest.fixture
def test_db_path(tmp_path):
    """Provides a path to an isolated temporary SQLite database."""
    return str(tmp_path / "test_spendly.db")


@pytest.fixture
def app_with_db(tmp_path):
    """Configures the Flask app to use an isolated temporary database."""
    db_file = str(tmp_path / "app_test.db")
    app.config["DATABASE"] = db_file
    app.config["TESTING"] = True

    with app.app_context():
        init_db(db_file)
        yield app, db_file
        close_db()


def test_get_db_foreign_keys_and_row_factory(test_db_path):
    """Verify that get_db enables foreign keys and sets row_factory to sqlite3.Row."""
    conn = get_db(test_db_path)
    try:
        # Check foreign_keys pragma
        fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk_status == 1, "Foreign keys should be enabled (PRAGMA foreign_keys = 1)"

        # Check row factory
        conn.execute("CREATE TABLE test_row (id INT, val TEXT);")
        conn.execute("INSERT INTO test_row VALUES (1, 'hello');")
        row = conn.execute("SELECT id, val FROM test_row;").fetchone()

        assert isinstance(row, sqlite3.Row)
        assert row["id"] == 1
        assert row["val"] == "hello"
        assert row[0] == 1
        assert row[1] == "hello"
    finally:
        conn.close()


def test_init_db_creates_tables(test_db_path):
    """Verify that init_db creates users, categories, and expenses tables."""
    init_db(test_db_path)

    conn = get_db(test_db_path)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row["name"] for row in cursor.fetchall()}
        assert "users" in tables
        assert "categories" in tables
        assert "expenses" in tables
    finally:
        conn.close()


def test_foreign_key_enforcement(test_db_path):
    """Verify that inserting an expense with a non-existent user_id raises sqlite3.IntegrityError."""
    init_db(test_db_path)

    conn = get_db(test_db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO expenses (user_id, amount, description, date)
                VALUES (9999, 100.0, 'Invalid user expense', '2026-11-20')
                """
            )
            conn.commit()
    finally:
        conn.close()


def test_cascade_delete_user(test_db_path):
    """Verify that deleting a user cascades to deleting their expenses."""
    init_db(test_db_path)

    conn = get_db(test_db_path)
    try:
        # Create user
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES ('Bob', 'bob@example.com', 'hash')"
        )
        user_id = cursor.lastrowid

        # Create expense
        conn.execute(
            "INSERT INTO expenses (user_id, amount, description, date) VALUES (?, 50.0, 'Coffee', '2026-11-20')",
            (user_id,),
        )
        conn.commit()

        # Delete user
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

        # Verify expense is also deleted
        count = conn.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)).fetchone()[0]
        assert count == 0, "Expense should be deleted via ON DELETE CASCADE"
    finally:
        conn.close()


def test_seed_db_data_and_password_hashing(test_db_path):
    """Verify seed_db populates categories, demo user, hashed password, and sample expenses."""
    seed_db(test_db_path)

    conn = get_db(test_db_path)
    try:
        # Categories check
        cat_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        assert cat_count >= 7, "Default categories should be seeded"

        # Demo user check
        user = conn.execute("SELECT * FROM users WHERE email = 'nitish@example.com'").fetchone()
        assert user is not None
        assert user["name"] == "Nitish Kumar"
        assert check_password_hash(user["password_hash"], "password123"), "Password must be verified via check_password_hash"

        # Expenses check
        expenses = conn.execute("SELECT * FROM expenses WHERE user_id = ?", (user["id"],)).fetchall()
        assert len(expenses) >= 3, "Sample expenses should be seeded for demo user"
    finally:
        conn.close()


def test_seed_db_idempotency(test_db_path):
    """Verify that running seed_db multiple times does not duplicate records or cause errors."""
    seed_db(test_db_path)

    conn = get_db(test_db_path)
    try:
        user_count_1 = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        cat_count_1 = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        exp_count_1 = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    finally:
        conn.close()

    # Run seed_db again
    seed_db(test_db_path)

    conn = get_db(test_db_path)
    try:
        user_count_2 = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        cat_count_2 = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        exp_count_2 = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]

        assert user_count_1 == user_count_2, "User count should not change after re-seeding"
        assert cat_count_1 == cat_count_2, "Category count should not change after re-seeding"
        assert exp_count_1 == exp_count_2, "Expense count should not change after re-seeding"
    finally:
        conn.close()


def test_flask_cli_commands(tmp_path):
    """Verify flask init-db and flask seed-db commands execute successfully."""
    db_file = str(tmp_path / "cli_test.db")
    app.config["DATABASE"] = db_file

    runner = app.test_cli_runner()

    # Test init-db
    result_init = runner.invoke(args=["init-db"])
    assert result_init.exit_code == 0
    assert "Initialized the database." in result_init.output

    # Test seed-db
    result_seed = runner.invoke(args=["seed-db"])
    assert result_seed.exit_code == 0
    assert "Seeded the database." in result_seed.output

    # Verify database content created by CLI
    conn = get_db(db_file)
    try:
        user = conn.execute("SELECT email FROM users WHERE email = 'nitish@example.com'").fetchone()
        assert user is not None
        assert user["email"] == "nitish@example.com"
    finally:
        conn.close()
