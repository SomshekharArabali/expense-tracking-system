from flask import Flask, render_template
from database.db import close_db, init_db, seed_db, get_db

app = Flask(__name__)

# Register database context teardown
app.teardown_appcontext(close_db)


# ------------------------------------------------------------------ #
# CLI Commands                                                        #
# ------------------------------------------------------------------ #

@app.cli.command("init-db")
def init_db_command():
    """Create all database tables."""
    init_db()
    print("Initialized the database.")


@app.cli.command("seed-db")
def seed_db_command():
    """Seed database with default categories and sample data."""
    seed_db()
    print("Seeded the database.")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
