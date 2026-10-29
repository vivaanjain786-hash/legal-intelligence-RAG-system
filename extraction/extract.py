import sqlite3
import re
from pathlib import Path
from tqdm import tqdm
import pymupdf as fitz


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")

PDF_ROOT = BASE_DIR / "supreme_court_judgments"
DB_PATH = BASE_DIR / "data" / "legal_dataset.db"


# ============================================================
# YEAR EXTRACTION
# ============================================================

def extract_year(path: Path):
    """
    Extract a four-digit year from the PDF's folder path
    or filename.
    """

    for part in path.parts:

        if re.fullmatch(r"(19|20)\d{2}", part):
            return int(part)

    match = re.search(
        r"\b(19|20)\d{2}\b",
        path.name
    )

    if match:
        return int(match.group())

    return None


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(pdf_path: Path):

    document = fitz.open(pdf_path)

    text_parts = []

    for page in document:
        text_parts.append(
            page.get_text("text")
        )

    full_text = "\n".join(text_parts)

    pages = len(document)

    document.close()

    return full_text, pages


# ============================================================
# VALIDATION
# ============================================================

if not PDF_ROOT.exists():
    raise FileNotFoundError(
        f"PDF directory not found:\n{PDF_ROOT}"
    )

if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DB_PATH}"
    )


print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - FULL PDF EXTRACTION")
print("=" * 70)

print(f"PDF ROOT : {PDF_ROOT}")
print(f"DATABASE : {DB_PATH}")
print()


# ============================================================
# FIND ALL PDFs
# ============================================================

pdf_files = list(
    PDF_ROOT.rglob("*.pdf")
)

print(
    f"PDF files found: {len(pdf_files):,}"
)

print()


if not pdf_files:
    raise RuntimeError(
        "No PDF files were found."
    )


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()


# ============================================================
# EXISTING FILES
# ============================================================

cursor.execute("""
    SELECT filename
    FROM cases
""")

existing_files = {
    row[0]
    for row in cursor.fetchall()
}


print(
    f"Already in database: "
    f"{len(existing_files):,}"
)

print(
    f"Remaining to process: "
    f"{len(pdf_files) - len(existing_files):,}"
)

print()


# ============================================================
# STATISTICS
# ============================================================

inserted = 0
skipped = 0
failed = 0

failures = []


# ============================================================
# EXTRACTION LOOP
# ============================================================

for pdf_path in tqdm(
    pdf_files,
    desc="Extracting PDFs"
):

    # Store path relative to dataset root.
    #
    # This prevents collisions if two different folders
    # contain PDFs with the same filename.
    relative_filename = str(
        pdf_path.relative_to(PDF_ROOT)
    )

    # Normalize Windows separators for database consistency.
    relative_filename = relative_filename.replace(
        "\\",
        "/"
    )

    if relative_filename in existing_files:

        skipped += 1
        continue

    try:

        text, pages = extract_pdf_text(
            pdf_path
        )

        word_count = len(
            text.split()
        )

        year = extract_year(
            pdf_path
        )

        cursor.execute("""
            INSERT INTO cases (
                filename,
                year,
                pages,
                word_count,
                raw_text,
                clean_text,
                processed
            )
            VALUES (?, ?, ?, ?, ?, NULL, 0)
        """, (
            relative_filename,
            year,
            pages,
            word_count,
            text
        ))

        inserted += 1

        # Commit periodically so that an interruption
        # does not lose the entire extraction.
        if inserted % 100 == 0:
            conn.commit()

    except Exception as e:

        failed += 1

        failures.append(
            (
                relative_filename,
                str(e)
            )
        )


# Final commit
conn.commit()


# ============================================================
# DATABASE SUMMARY
# ============================================================

cursor.execute("""
    SELECT COUNT(*)
    FROM cases
""")

total_cases = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM cases
    WHERE raw_text IS NOT NULL
""")

extracted_cases = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM cases
    WHERE clean_text IS NOT NULL
""")

cleaned_cases = cursor.fetchone()[0]


conn.close()


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("EXTRACTION COMPLETE")
print("=" * 70)

print(
    f"PDF files found       : {len(pdf_files):,}"
)

print(
    f"Already existed       : {skipped:,}"
)

print(
    f"Successfully inserted : {inserted:,}"
)

print(
    f"Failed                : {failed:,}"
)

print(
    f"Cases in database     : {total_cases:,}"
)

print(
    f"Cases with raw text   : {extracted_cases:,}"
)

print(
    f"Cases with clean text : {cleaned_cases:,}"
)

print()


# ============================================================
# FAILURES
# ============================================================

if failures:

    print("=" * 70)
    print("FAILED FILES")
    print("=" * 70)

    for filename, error in failures:

        print()
        print(filename)
        print("ERROR:", error)


print()
print(
    f"Database: {DB_PATH}"
)

print()
print(
    "Next step: run clean_text.py"
)