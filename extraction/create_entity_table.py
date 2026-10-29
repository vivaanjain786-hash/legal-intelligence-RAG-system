import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS case_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    case_id INTEGER NOT NULL,

    entity_type TEXT NOT NULL,

    entity_text TEXT NOT NULL,

    normalized_text TEXT NOT NULL,

    FOREIGN KEY (case_id)
        REFERENCES cases(id)
        ON DELETE CASCADE,

    UNIQUE (
        case_id,
        entity_type,
        normalized_text
    )
)
""")


cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_entities_case_id
ON case_entities(case_id)
""")


cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_entities_type
ON case_entities(entity_type)
""")


cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_entities_normalized
ON case_entities(normalized_text)
""")


conn.commit()
conn.close()


print("=" * 65)
print("CASE ENTITIES TABLE")
print("=" * 65)
print(f"Database: {DB_PATH}")
print()
print("✓ case_entities table ready")
print("✓ Indexes created")
print()