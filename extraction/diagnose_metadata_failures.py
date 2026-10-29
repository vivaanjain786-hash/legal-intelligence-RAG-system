import sqlite3
import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"

sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


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

success = Counter()
failures = Counter()
examples = {}

for case_id, filename, text in cases:

    parser = factory.get_parser(text)

    if parser is None:
        continue

    parser_name = parser.__class__.__name__

    try:
        result = parser.parse(text)

        if result is None:
            failures[(parser_name, "RETURNED_NONE")] += 1

            examples.setdefault(
                (parser_name, "RETURNED_NONE"),
                (case_id, filename)
            )

        else:
            success[parser_name] += 1

    except Exception as e:

        error_type = type(e).__name__
        error_message = str(e)

        key = (parser_name, error_type)

        failures[key] += 1

        examples.setdefault(
            key,
            (case_id, filename, error_message)
        )


conn.close()


print("=" * 75)
print("METADATA PARSER FAILURE DIAGNOSTIC")
print("=" * 75)

print()
print("SUCCESSFUL PARSES")
print("-" * 50)

for parser, count in success.items():
    print(f"{parser:25} : {count:,}")


print()
print("FAILURES BY PARSER / ERROR")
print("-" * 75)

for (parser, error_type), count in failures.most_common():

    print()
    print(f"Parser      : {parser}")
    print(f"Error       : {error_type}")
    print(f"Count       : {count:,}")

    example = examples[(parser, error_type)]

    print(f"Example ID  : {example[0]}")
    print(f"Example file: {example[1]}")

    if len(example) >= 3:
        print(f"Message     : {example[2]}")


print()
print("=" * 75)
print("TOTAL FAILURES:", sum(failures.values()))
print("=" * 75)