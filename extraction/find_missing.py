import sqlite3
from pathlib import Path


BASE_DIR = Path(
    r"C:\Users\Vivaan Jain\Downloads\Legal Dataset"
)

PDF_ROOT = BASE_DIR / "supreme_court_judgments"
DB_PATH = BASE_DIR / "data" / "legal_dataset.db"


def normalize(path):
    path = path.replace("\\", "/")

    prefix = "supreme_court_judgments/"

    if path.startswith(prefix):
        path = path[len(prefix):]

    return path


print("=" * 70)
print("NORMALIZED PDF ↔ DATABASE CHECK")
print("=" * 70)


# ============================================================
# PDFs ON DISK
# ============================================================

disk_files = set()

for pdf_path in PDF_ROOT.rglob("*.pdf"):

    relative = str(
        pdf_path.relative_to(PDF_ROOT)
    ).replace("\\", "/")

    disk_files.add(
        normalize(relative)
    )


print(f"PDFs on disk: {len(disk_files):,}")


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT id, filename
    FROM cases
""")

db_files = {}

for case_id, filename in cursor.fetchall():

    normalized = normalize(filename)

    db_files[normalized] = case_id

conn.close()


print(f"Database records: {len(db_files):,}")


# ============================================================
# COMPARE
# ============================================================

missing = disk_files - set(db_files.keys())

extra = set(db_files.keys()) - disk_files


print()
print("=" * 70)
print("RESULT")
print("=" * 70)

print(
    f"Missing from database : {len(missing):,}"
)

print(
    f"Extra in database     : {len(extra):,}"
)


# ============================================================
# MISSING
# ============================================================

if missing:

    print()
    print("=" * 70)
    print("MISSING PDFS")
    print("=" * 70)

    for filename in sorted(missing):
        print(filename)


# ============================================================
# EXTRA
# ============================================================

if extra:

    print()
    print("=" * 70)
    print("EXTRA DATABASE RECORDS")
    print("=" * 70)

    for filename in sorted(extra):

        print(
            f"ID={db_files[filename]} | {filename}"
        )


print()
print("=" * 70)
print("CHECK COMPLETE")
print("=" * 70)