import sqlite3
from pathlib import Path
from tqdm import tqdm


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


# ============================================================
# SETTINGS
# ============================================================

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Test first.
TEST_LIMIT = 26622



# ============================================================
# CHUNK FUNCTION
# ============================================================

def create_chunks(text, chunk_size=1000, overlap=200):
    """
    Split text into overlapping word-based chunks.

    Example:

        chunk size = 1000 words
        overlap    = 200 words

    Chunk 1:
        words 0 - 999

    Chunk 2:
        words 800 - 1799

    Chunk 3:
        words 1600 - 2599
    """

    words = text.split()

    if not words:
        return []

    chunks = []

    start = 0
    chunk_index = 0

    step = chunk_size - overlap

    while start < len(words):

        end = min(
            start + chunk_size,
            len(words)
        )

        chunk_words = words[start:end]

        chunk_text = " ".join(chunk_words)

        chunks.append({
            "chunk_index": chunk_index,
            "text": chunk_text,
            "word_count": len(chunk_words),
            "start_word": start,
            "end_word": end
        })

        chunk_index += 1

        if end >= len(words):
            break

        start += step

    return chunks


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
    LIMIT ?
""", (TEST_LIMIT,))

cases = cursor.fetchall()


print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - DOCUMENT CHUNKING")
print("=" * 70)

print(f"Database       : {DB_PATH}")
print(f"Test cases     : {len(cases)}")
print(f"Chunk size     : {CHUNK_SIZE} words")
print(f"Chunk overlap  : {CHUNK_OVERLAP} words")
print()


# ============================================================
# STATISTICS
# ============================================================

total_chunks = 0
failed_cases = 0


# ============================================================
# PROCESS
# ============================================================

for case_id, filename, text in tqdm(
    cases,
    desc="Creating chunks"
):

    try:

        chunks = create_chunks(
            text,
            CHUNK_SIZE,
            CHUNK_OVERLAP
        )

        for chunk in chunks:

            cursor.execute("""
                INSERT OR IGNORE INTO chunks (
                    case_id,
                    chunk_index,
                    text,
                    word_count,
                    start_word,
                    end_word
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                chunk["chunk_index"],
                chunk["text"],
                chunk["word_count"],
                chunk["start_word"],
                chunk["end_word"]
            ))

            total_chunks += 1

    except Exception as e:

        failed_cases += 1

        print()
        print("-" * 70)
        print("ERROR")
        print(f"Case ID : {case_id}")
        print(f"File    : {filename}")
        print(f"Error   : {e}")
        print("-" * 70)


conn.commit()


# ============================================================
# DATABASE STATISTICS
# ============================================================

cursor.execute("""
    SELECT COUNT(*)
    FROM chunks
""")

database_chunks = cursor.fetchone()[0]


cursor.execute("""
    SELECT
        COUNT(*),
        AVG(word_count),
        MIN(word_count),
        MAX(word_count)
    FROM chunks
""")

count, average_words, minimum_words, maximum_words = cursor.fetchone()


conn.close()


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 70)
print("CHUNKING TEST COMPLETE")
print("=" * 70)

print(f"Cases processed       : {len(cases):,}")
print(f"Chunks created        : {total_chunks:,}")
print(f"Failed cases          : {failed_cases:,}")

print()
print("DATABASE")
print("-" * 40)

print(f"Total chunks          : {database_chunks:,}")
print(f"Average words/chunk   : {average_words:.2f}")
print(f"Minimum words/chunk   : {minimum_words}")
print(f"Maximum words/chunk   : {maximum_words}")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)