import sqlite3
import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT clean_text
    FROM cases
    WHERE clean_text IS NOT NULL
""")

rows = cursor.fetchall()

conn.close()

factory = ParserFactory()
counts = Counter()

for (text,) in rows:

    parser = factory.get_parser(text)

    if parser is None:
        counts["UNKNOWN"] += 1
    else:
        counts[parser.__class__.__name__] += 1


print("=" * 70)
print("PARSER DISTRIBUTION")
print("=" * 70)

total = len(rows)

for name in [
    "ModernParser",
    "OldStructuredParser",
    "OldMinimalParser",
    "UNKNOWN"
]:

    count = counts[name]

    percentage = count / total * 100

    print(
        f"{name:22}: {count:7,} "
        f"({percentage:6.2f}%)"
    )

print("-" * 70)
print(
    f"{'TOTAL':22}: {total:7,}"
)