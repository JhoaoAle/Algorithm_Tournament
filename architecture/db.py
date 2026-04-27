import sqlite3
from pathlib import Path

# -----------------------------
# PATH CONFIG
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "tournament_results" / "tournament.db"


# -----------------------------
# CONNECTION HELPER
# -----------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# -----------------------------
# INIT DB
# -----------------------------
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            iteration INTEGER,
            competitor_a TEXT,
            competitor_b TEXT,
            score_a REAL,
            score_b REAL,
            rounds INTEGER
        )
        """)


        cur.execute("""
        CREATE TABLE IF NOT EXISTS match_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER,
            iteration INTEGER,
            round INTEGER,
            competitor_a TEXT,
            competitor_b TEXT,
            action_a TEXT,
            action_b TEXT
        )
        """)


        cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_iteration ON matches(iteration)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_actions_match_id ON match_actions(match_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_actions_iteration ON match_actions(iteration)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_actions_comp_a ON match_actions(competitor_a)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_actions_comp_b ON match_actions(competitor_b)")

        conn.commit()



def insert_match(conn, iteration, competitor_a, competitor_b, score_a, score_b, rounds):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO matches (
            iteration, competitor_a, competitor_b,
            score_a, score_b, rounds
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (iteration, competitor_a, competitor_b, score_a, score_b, rounds))

    return cur.lastrowid



def insert_actions(conn, rows):
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO match_actions (
            match_id, iteration, round,
            competitor_a, competitor_b,
            action_a, action_b
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)