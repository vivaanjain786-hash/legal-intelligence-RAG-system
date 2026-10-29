import sqlite3
import sys
import json
from pathlib import Path
from tqdm import tqdm


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"

sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


# ============================================================
# HELPERS
# ============================================================

def prepare_value(value):
    """
    Convert parser output into a SQLite-safe value.

    Strings, integers, floats and None are stored directly.
    Lists/dictionaries are stored as JSON strings.
    """

    if value is None:
        return None

    if isinstance(value, (list, dict)):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return value


# ============================================================
# DATABASE
# ============================================================

if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DB_PATH}"
    )


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ============================================================
# LOAD CASES
# ============================================================

cursor.execute("""
    SELECT
        id,
        filename,
        clean_text
    FROM cases
    WHERE clean_text IS NOT NULL
    ORDER BY id
""")

cases = cursor.fetchall()


print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - METADATA EXTRACTION")
print("=" * 70)
print(f"Database : {DB_PATH}")
print(f"Cases    : {len(cases):,}")
print()


# ============================================================
# INITIALIZE
# ============================================================

factory = ParserFactory()

processed = 0
inserted = 0
unknown = 0
skipped = 0
failed = 0


# ============================================================
# PROCESS CASES
# ============================================================

for case_id, filename, text in tqdm(
    cases,
    desc="Extracting metadata"
):

    processed += 1

    try:

        # ----------------------------------------------------
        # Check whether metadata already exists
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM metadata
            WHERE case_id = ?
            LIMIT 1
        """, (case_id,))

        if cursor.fetchone():
            skipped += 1
            continue


        # ----------------------------------------------------
        # Find parser
        # ----------------------------------------------------

        parser = factory.get_parser(text)

        if parser is None:
            unknown += 1
            continue


        # ----------------------------------------------------
        # Extract metadata
        # ----------------------------------------------------

        data = parser.parse(text)

        if not data:
            unknown += 1
            continue


        # ----------------------------------------------------
        # Parser format
        # ----------------------------------------------------

        parser_format = parser.__class__.__name__


        # ----------------------------------------------------
        # Insert metadata
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO metadata (
                case_id,
                format,
                title,
                decision_date,
                court,
                citation,
                case_type,
                case_number,
                author,
                bench,
                judge,
                petitioner,
                respondent,
                reportable,
                acts,
                articles
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            case_id,

            parser_format,

            prepare_value(data.get("title")),
            prepare_value(data.get("decision_date")),
            prepare_value(data.get("court")),
            prepare_value(data.get("citation")),
            prepare_value(data.get("case_type")),
            prepare_value(data.get("case_number")),

            prepare_value(data.get("author")),
            prepare_value(data.get("bench")),
            prepare_value(data.get("judge")),

            prepare_value(data.get("petitioner")),
            prepare_value(data.get("respondent")),

            prepare_value(data.get("reportable")),

            prepare_value(data.get("acts")),
            prepare_value(data.get("articles"))
        ))

        inserted += 1


    except Exception as e:

        failed += 1

        print()
        print("-" * 70)
        print(f"ERROR processing case {case_id}")
        print(f"FILE: {filename}")
        print(f"ERROR: {e}")
        print("-" * 70)


    # Commit periodically so a long run doesn't lose everything
    if processed % 500 == 0:
        conn.commit()


# Final commit
conn.commit()


# ============================================================
# FINAL STATISTICS
# ============================================================

cursor.execute("""
    SELECT COUNT(*)
    FROM metadata
""")

total_metadata = cursor.fetchone()[0]


cursor.execute("""
    SELECT format, COUNT(*)
    FROM metadata
    GROUP BY format
    ORDER BY format
""")

format_counts = cursor.fetchall()


conn.close()


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 70)
print("METADATA EXTRACTION COMPLETE")
print("=" * 70)

print(f"Cases processed       : {processed:,}")
print(f"Metadata inserted     : {inserted:,}")
print(f"Already existing      : {skipped:,}")
print(f"Unknown parser        : {unknown:,}")
print(f"Failed                : {failed:,}")
print(f"Total metadata rows   : {total_metadata:,}")

print()
print("FORMAT DISTRIBUTION")
print("-" * 40)

for format_name, count in format_counts:
    print(f"{format_name:25} : {count:,}")

print()
print("=" * 70)
print("Database updated successfully.")
print("=" * 70)