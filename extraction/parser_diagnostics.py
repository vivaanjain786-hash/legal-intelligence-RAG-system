import sqlite3
import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - FULL PARSER DIAGNOSTIC")
print("=" * 70)

print(f"Database: {DB_PATH}")
print()


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT id, filename, clean_text
    FROM cases
    WHERE clean_text IS NOT NULL
    ORDER BY id
""")

cases = cursor.fetchall()

print(f"Cleaned cases found: {len(cases):,}")
print()


# ============================================================
# PARSER
# ============================================================

factory = ParserFactory()

counts = Counter()

unknown_cases = []

failures = []


# ============================================================
# CLASSIFICATION
# ============================================================

for case_id, filename, text in cases:

    try:

        parser = factory.get_parser(text)

        if parser is None:

            parser_name = "UNKNOWN"

            unknown_cases.append(
                (
                    case_id,
                    filename,
                    len(text)
                )
            )

        else:

            parser_name = parser.__class__.__name__

        counts[parser_name] += 1

    except Exception as e:

        counts["ERROR"] += 1

        failures.append(
            (
                case_id,
                filename,
                str(e)
            )
        )


conn.close()


# ============================================================
# RESULTS
# ============================================================

total = len(cases)

print("=" * 70)
print("PARSER DISTRIBUTION")
print("=" * 70)

for parser_name in [
    "ModernParser",
    "OldStructuredParser",
    "OldMinimalParser",
    "UNKNOWN",
    "ERROR"
]:

    count = counts.get(parser_name, 0)

    percentage = (
        count / total * 100
        if total
        else 0
    )

    print(
        f"{parser_name:22} : "
        f"{count:7,} "
        f"({percentage:6.2f}%)"
    )


print()
print(
    f"{'TOTAL':22} : "
    f"{total:7,}"
)


# ============================================================
# UNKNOWN CASES
# ============================================================

print()
print("=" * 70)
print("UNKNOWN CASES")
print("=" * 70)

print(
    f"Unknown cases: {len(unknown_cases):,}"
)

print()

for case_id, filename, text_length in unknown_cases[:100]:

    print(
        f"ID={case_id} | "
        f"TEXT={text_length:,} | "
        f"{filename}"
    )


if len(unknown_cases) > 100:

    print()
    print(
        f"... and "
        f"{len(unknown_cases) - 100:,} more."
    )


# ============================================================
# ERRORS
# ============================================================

if failures:

    print()
    print("=" * 70)
    print("PARSER ERRORS")
    print("=" * 70)

    for case_id, filename, error in failures[:100]:

        print()
        print(f"ID: {case_id}")
        print(f"FILE: {filename}")
        print(f"ERROR: {error}")


print()
print("=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)