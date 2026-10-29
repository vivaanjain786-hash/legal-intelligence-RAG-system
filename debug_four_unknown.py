import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("DATABASE RECORDS: 1991-1993")
print("=" * 70)

cursor.execute("""
    SELECT id, year, filename, length(clean_text)
    FROM cases
    WHERE year BETWEEN 1991 AND 1993
    ORDER BY year, id
""")

rows = cursor.fetchall()

print(f"Records found: {len(rows)}")
print()

for case_id, year, filename, text_length in rows:
    print(
        f"ID={case_id} | "
        f"YEAR={year} | "
        f"TEXT={text_length} | "
        f"{filename}"
    )

conn.close()