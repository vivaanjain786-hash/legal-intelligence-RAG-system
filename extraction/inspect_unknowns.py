import sqlite3
import sys
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT id, filename, clean_text
    FROM cases
    WHERE clean_text IS NOT NULL
    ORDER BY id
""")

cases = cursor.fetchall()

factory = ParserFactory()

unknowns = []


for case_id, filename, text in cases:

    parser = factory.get_parser(text)

    if parser is None:

        first = text[:3000]

        unknowns.append(
            (
                case_id,
                filename,
                len(text),
                first
            )
        )


conn.close()


print("=" * 80)
print("UNKNOWN PARSER DIAGNOSTIC")
print("=" * 80)

print(f"UNKNOWN CASES: {len(unknowns)}")
print()


for case_id, filename, text_length, first in unknowns:

    print()
    print("=" * 80)
    print(
        f"ID: {case_id} | "
        f"TEXT LENGTH: {text_length:,}"
    )
    print(f"FILE: {filename}")
    print("-" * 80)

    # Print first 30 lines only
    lines = first.splitlines()

    for i, line in enumerate(lines[:30], start=1):

        line = line.strip()

        if line:
            print(
                f"{i:02}: {line}"
            )

    print()