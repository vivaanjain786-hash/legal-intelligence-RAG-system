import sqlite3
from pathlib import Path

DB_PATH = Path(
    r"C:\Users\Vivaan Jain\Downloads\Legal Dataset\data\legal_dataset.db"
)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT
    id,
    filename,
    year,
    pages,
    word_count,
    LENGTH(raw_text)
FROM cases
ORDER BY id
LIMIT 5
""")

rows = cursor.fetchall()

print("=" * 80)
print("DATABASE TEST")
print("=" * 80)

for row in rows:
    print()
    print(f"ID         : {row[0]}")
    print(f"Filename   : {row[1]}")
    print(f"Year       : {row[2]}")
    print(f"Pages      : {row[3]}")
    print(f"Word count : {row[4]}")
    print(f"Text chars : {row[5]}")

    cursor.execute(
        """
        SELECT raw_text
        FROM cases
        WHERE id = ?
        """,
        (row[0],)
    )

    text = cursor.fetchone()[0]

    print()
    print("FIRST 1000 CHARACTERS")
    print("-" * 80)
    print(text[:1000])
    print("-" * 80)

conn.close()