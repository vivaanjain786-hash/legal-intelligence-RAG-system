import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    case_id INTEGER NOT NULL,

    chunk_index INTEGER NOT NULL,

    text TEXT NOT NULL,

    word_count INTEGER NOT NULL,

    start_word INTEGER NOT NULL,

    end_word INTEGER NOT NULL,

    FOREIGN KEY (case_id)
        REFERENCES cases(id)
        ON DELETE CASCADE,

    UNIQUE (
        case_id,
        chunk_index
    )
)
""")


cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_chunks_case_id
ON chunks(case_id)
""")


cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index
ON chunks(chunk_index)
""")


conn.commit()
conn.close()


print("=" * 65)
print("CHUNKS TABLE")
print("=" * 65)
print(f"Database: {DB_PATH}")
print()
print("✓ chunks table ready")
print("✓ indexes created")
print()