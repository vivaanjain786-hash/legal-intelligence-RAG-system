import sqlite3
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "legal_dataset.db"

DB_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("LEGAL INTELLIGENCE SYSTEM - DATABASE SETUP")
print("=" * 60)
print(f"Database: {DB_PATH}")
print()


# ============================================================
# SAFETY CHECK
# ============================================================

if DB_PATH.exists():
    print("⚠️ Database already exists.")
    print("This script will NOT overwrite it.")
    print()
    print("If this is an existing database, inspect it before")
    print("creating anything new.")
    raise SystemExit


# ============================================================
# CONNECT
# ============================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ============================================================
# CASES TABLE
# ============================================================

cursor.execute("""
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    year INTEGER,
    pages INTEGER,
    word_count INTEGER,
    raw_text TEXT,
    clean_text TEXT,
    processed INTEGER DEFAULT 0
)
""")


# ============================================================
# METADATA TABLE
# ============================================================

cursor.execute("""
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,

    format TEXT,
    title TEXT,
    decision_date TEXT,
    court TEXT,
    citation TEXT,
    case_type TEXT,
    case_number TEXT,

    author TEXT,
    bench TEXT,
    judge TEXT,

    petitioner TEXT,
    respondent TEXT,

    reportable TEXT,

    acts TEXT,
    articles TEXT,

    FOREIGN KEY (case_id)
        REFERENCES cases(id)
        ON DELETE CASCADE
)
""")


# ============================================================
# INDEXES
# ============================================================

cursor.execute("""
CREATE INDEX idx_cases_year
ON cases(year)
""")

cursor.execute("""
CREATE INDEX idx_cases_processed
ON cases(processed)
""")

cursor.execute("""
CREATE INDEX idx_metadata_case_id
ON metadata(case_id)
""")

cursor.execute("""
CREATE INDEX idx_metadata_format
ON metadata(format)
""")

cursor.execute("""
CREATE INDEX idx_metadata_citation
ON metadata(citation)
""")


# ============================================================
# COMMIT
# ============================================================

conn.commit()
conn.close()


# ============================================================
# VERIFY
# ============================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

tables = cursor.fetchall()

print("Created tables:")
for table in tables:
    print(f"  ✓ {table[0]}")

conn.close()

print()
print("=" * 60)
print("✅ DATABASE CREATED SUCCESSFULLY")
print("=" * 60)
print(f"Location: {DB_PATH}")