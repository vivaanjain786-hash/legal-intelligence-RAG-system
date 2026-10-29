import sqlite3
import sys
from pathlib import Path

# Allow imports from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ============================================================
# LOAD CASES
# ============================================================

cursor.execute("""
    SELECT id, filename, clean_text
    FROM cases
    WHERE clean_text IS NOT NULL
    ORDER BY id
""")

cases = cursor.fetchall()

print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - PARSER TEST")
print("=" * 70)

print(f"Cases available: {len(cases)}")
print()


# ============================================================
# FACTORY
# ============================================================

factory = ParserFactory()


# ============================================================
# PARSE
# ============================================================

for case_id, filename, text in cases:

    parser = factory.get_parser(text)

    print("-" * 70)
    print(f"CASE ID : {case_id}")
    print(f"FILE    : {filename}")

    if parser is None:

        print("PARSER  : UNKNOWN")
        continue

    print(
        f"PARSER  : {parser.__class__.__name__}"
    )

    metadata = parser.parse(text)

    print()
    print("METADATA")

    for key, value in metadata.items():

        print(
            f"{key:15}: {value}"
        )

print()
print("=" * 70)
print("PARSER TEST COMPLETE")
print("=" * 70)

conn.close()