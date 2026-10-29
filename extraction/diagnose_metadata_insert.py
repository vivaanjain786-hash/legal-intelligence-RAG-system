import sqlite3
import sys
import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"

sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


def prepare_value(value):
    if value is None:
        return None

    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)

    return value


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

failures = Counter()
examples = {}

successful_inserts = 0
unknown = 0


for case_id, filename, text in cases:

    parser = factory.get_parser(text)

    if parser is None:
        unknown += 1
        continue

    try:

        data = parser.parse(text)

        values = (
            case_id,
            parser.__class__.__name__,
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
        )

        # Test the exact same INSERT used by extract_metadata.py.
        # Roll it back immediately so the database is NOT changed.

        cursor.execute("SAVEPOINT metadata_test")

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
        """, values)

        cursor.execute("ROLLBACK TO metadata_test")
        cursor.execute("RELEASE metadata_test")

        successful_inserts += 1

    except Exception as e:

        try:
            cursor.execute("ROLLBACK TO metadata_test")
            cursor.execute("RELEASE metadata_test")
        except Exception:
            pass

        error_type = type(e).__name__
        error_message = str(e)

        key = (parser.__class__.__name__, error_type, error_message)

        failures[key] += 1

        if key not in examples:
            examples[key] = (
                case_id,
                filename
            )


conn.rollback()
conn.close()


print("=" * 75)
print("METADATA INSERT DIAGNOSTIC")
print("=" * 75)

print()
print(f"Cases checked       : {len(cases):,}")
print(f"Successful inserts  : {successful_inserts:,}")
print(f"Unknown             : {unknown:,}")
print(f"Insert failures     : {sum(failures.values()):,}")

print()
print("FAILURES")
print("-" * 75)

for (parser, error_type, message), count in failures.most_common():

    case_id, filename = examples[(parser, error_type, message)]

    print()
    print(f"Parser      : {parser}")
    print(f"Error type  : {error_type}")
    print(f"Count       : {count:,}")
    print(f"Message     : {message}")
    print(f"Example ID  : {case_id}")
    print(f"Example file: {filename}")

print()
print("=" * 75)
print("DIAGNOSTIC COMPLETE")
print("=" * 75)