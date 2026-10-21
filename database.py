import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("ecovision.db")

def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    db.commit()
    # Add demonstration data only to a new empty reports table.
    count = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0 and users_count == 0:
        demo = [
            ("Plastic waste near the lake", "Waste", "Green Lake Park", "Several plastic bottles and wrappers were observed along the walking path.", "Open"),
            ("Dust and smoke near junction", "Pollution", "Central Junction", "Community members noticed dust and smoke during peak traffic.", "In progress"),
            ("Public tap water pooling", "Water", "Market Street", "Water is pooling around a public tap and may need inspection.", "Resolved"),
        ]
        cur = db.execute("INSERT INTO users (name,email,password_hash) VALUES (?,?,?)",
                         ("EcoVision Community", "community@example.com", "demo-account-no-login"))
        uid = cur.lastrowid
        db.executemany("INSERT INTO reports (user_id,title,category,location,description,status) VALUES (?,?,?,?,?,?)",
                       [(uid, *row) for row in demo])
        db.commit()
    db.close()
