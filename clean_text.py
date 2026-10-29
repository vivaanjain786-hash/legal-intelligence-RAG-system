import sqlite3
import re
import unicodedata
from tqdm import tqdm
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")
DB_PATH = BASE_DIR / "data" / "legal_dataset.db"


# ============================================================
# DATABASE
# ============================================================

print("Using database:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ============================================================
# GET UNPROCESSED CASES
# ============================================================

cursor.execute("""
    SELECT id, raw_text
    FROM cases
    WHERE processed = 0
""")

rows = cursor.fetchall()

print(f"Found {len(rows)} judgments to clean.")


# ============================================================
# CLEAN TEXT
# ============================================================

for case_id, text in tqdm(rows, desc="Cleaning judgments"):

    if not text:
        continue

    # --------------------------------------------------------
    # Unicode normalization
    # --------------------------------------------------------

    text = unicodedata.normalize("NFKC", text)

    # --------------------------------------------------------
    # Remove URLs
    # --------------------------------------------------------

    text = re.sub(r"https?://\S+", "", text)

    # --------------------------------------------------------
    # Remove tabs
    # --------------------------------------------------------

    text = text.replace("\t", " ")

    # --------------------------------------------------------
    # Remove control characters
    # --------------------------------------------------------

    text = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F]",
        "",
        text
    )

    # --------------------------------------------------------
    # Collapse multiple spaces
    # --------------------------------------------------------

    text = re.sub(r"[ ]{2,}", " ", text)

    # --------------------------------------------------------
    # Normalize blank lines
    # --------------------------------------------------------

    text = re.sub(r"\n{3,}", "\n\n", text)

    # --------------------------------------------------------
    # Trim
    # --------------------------------------------------------

    text = text.strip()

    # --------------------------------------------------------
    # Update database
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE cases
        SET clean_text = ?,
            processed = 1
        WHERE id = ?
    """, (text, case_id))


# ============================================================
# COMMIT
# ============================================================

conn.commit()
conn.close()

print()
print("✅ Cleaning completed.")