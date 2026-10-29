import sqlite3
import re
import hashlib
from contextlib import closing
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"
CHROMA_PATH = PROJECT_ROOT / "vector_db"


# ============================================================
# MODELS
# ============================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

COLLECTION_NAME = "legal_judgments"


# ============================================================
# SEARCH SETTINGS
# ============================================================

# Number of chunks initially retrieved from ChromaDB
RETRIEVAL_K = 30

# Number of final unique cases returned
DISPLAY_RESULTS = 8

# Neighboring chunks retained internally for RAG
CONTEXT_BEFORE = 1
CONTEXT_AFTER = 1


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_pdf_text(text):
    """
    Clean common PDF extraction artifacts.

    This does NOT modify SQLite or ChromaDB.
    """

    if not text:
        return ""

    # Fix PDF hyphenation
    # Example:
    # Consti-
    # tution
    # becomes:
    # Constitution
    text = re.sub(
        r"([A-Za-z])-\s+([A-Za-z])",
        r"\1\2",
        text
    )

    # Remove remaining line breaks
    text = re.sub(
        r"\s*\n\s*",
        " ",
        text
    )

    # Collapse repeated whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CONTENT HASH
# ============================================================

def get_content_hash(text):
    """
    Generate a fingerprint for the judgment.

    Used to detect duplicate judgments with different IDs.
    """

    cleaned = clean_pdf_text(text)

    return hashlib.sha256(
        cleaned.encode("utf-8")
    ).hexdigest()


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Embedding model loaded")


# ============================================================
# LOAD RERANKER
# ============================================================

print()
print("Loading reranker...")

reranker = CrossEncoder(
    RERANKER_MODEL
)

print("Reranker loaded")


# ============================================================
# CONNECT CHROMADB
# ============================================================

print()
print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print(
    f"ChromaDB connected "
    f"({collection.count():,} vectors)"
)


# ============================================================
# GET CASE
# ============================================================

def get_case(cursor, case_id):

    cursor.execute(
        """
        SELECT
            filename,
            year,
            raw_text
        FROM cases
        WHERE id = ?
        """,
        (case_id,)
    )

    return cursor.fetchone()


# ============================================================
# GET MATCHED CHUNK
# ============================================================

def get_chunk(cursor, case_id, chunk_index):

    cursor.execute(
        """
        SELECT
            text
        FROM chunks
        WHERE case_id = ?
          AND chunk_index = ?
        """,
        (
            case_id,
            chunk_index
        )
    )

    row = cursor.fetchone()

    if row:
        return clean_pdf_text(row[0])

    return ""


# ============================================================
# GET SURROUNDING CONTEXT
# ============================================================

def get_context(cursor, case_id, chunk_index):

    start_chunk = max(
        0,
        chunk_index - CONTEXT_BEFORE
    )

    end_chunk = (
        chunk_index
        + CONTEXT_AFTER
    )

    cursor.execute(
        """
        SELECT
            chunk_index,
            text
        FROM chunks
        WHERE case_id = ?
          AND chunk_index BETWEEN ? AND ?
        ORDER BY chunk_index
        """,
        (
            case_id,
            start_chunk,
            end_chunk
        )
    )

    rows = cursor.fetchall()

    context_parts = []

    for _, text in rows:

        cleaned = clean_pdf_text(text)

        if cleaned:
            context_parts.append(cleaned)

    return " ".join(context_parts)


# ============================================================
# SEARCH
# ============================================================

def search(query):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        return _search(query, conn.cursor())


def _search(query, cursor):

    # ========================================================
    # STAGE 1
    # VECTOR RETRIEVAL
    # ========================================================

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=RETRIEVAL_K
    )

    result_ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]


    # ========================================================
    # BUILD ALL CANDIDATES
    # ========================================================

    candidates = []

    for i in range(len(result_ids)):

        metadata = metadatas[i]

        case_id = int(
            metadata["case_id"]
        )

        chunk_index = int(
            metadata["chunk_index"]
        )


        # ----------------------------------------------------
        # Get case information
        # ----------------------------------------------------

        case = get_case(cursor, case_id)

        if case:

            filename, year, raw_text = case

        else:

            filename = metadata.get(
                "filename",
                "Unknown"
            )

            year = metadata.get(
                "year",
                -1
            )

            raw_text = ""


        # ----------------------------------------------------
        # Get ACTUAL matched chunk
        # ----------------------------------------------------

        matched_chunk = get_chunk(
            cursor,
            case_id,
            chunk_index
        )

        if not matched_chunk:
            continue


        # ----------------------------------------------------
        # Store candidate
        # ----------------------------------------------------

        candidates.append({

            "chunk_id":
                int(result_ids[i]),

            "case_id":
                case_id,

            "filename":
                filename,

            "year":
                year,

            "chunk_index":
                chunk_index,

            "embedding_distance":
                distances[i],

            "matched_chunk":
                matched_chunk,

            "raw_text":
                raw_text,

            "content_hash":
                get_content_hash(raw_text)
        })


    # ========================================================
    # STAGE 2
    # CROSS-ENCODER RERANKING
    # ========================================================

    if not candidates:
        return []


    # --------------------------------------------------------
    # Create query/chunk pairs
    # --------------------------------------------------------

    pairs = []

    for candidate in candidates:

        pairs.append([
            query,
            candidate["matched_chunk"]
        ])


    print(
        f"Reranking "
        f"{len(pairs)} candidate chunks..."
    )


    # --------------------------------------------------------
    # Score ALL candidates
    # --------------------------------------------------------

    scores = reranker.predict(
        pairs
    )


    # --------------------------------------------------------
    # Attach reranker scores
    # --------------------------------------------------------

    for candidate, score in zip(
        candidates,
        scores
    ):

        candidate["reranker_score"] = float(
            score
        )


    # --------------------------------------------------------
    # Sort by reranker score
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: x["reranker_score"],
        reverse=True
    )


    # ========================================================
    # STAGE 3
    # DEDUPLICATE AFTER RERANKING
    # ========================================================

    final_candidates = []

    seen_content = set()
    seen_cases = set()


    for candidate in candidates:

        content_hash = candidate[
            "content_hash"
        ]

        case_id = candidate[
            "case_id"
        ]


        # ----------------------------------------------------
        # Remove duplicate judgment content
        # ----------------------------------------------------

        if content_hash in seen_content:
            continue


        # ----------------------------------------------------
        # Remove another chunk from same case
        # ----------------------------------------------------

        if case_id in seen_cases:
            continue


        seen_content.add(
            content_hash
        )

        seen_cases.add(
            case_id
        )


        final_candidates.append(
            candidate
        )


        # ----------------------------------------------------
        # Stop after enough unique cases
        # ----------------------------------------------------

        if len(final_candidates) >= DISPLAY_RESULTS:
            break


    # ========================================================
    # STAGE 4
    # ADD RAG CONTEXT
    # ========================================================

    output = []


    for candidate in final_candidates:

        full_context = get_context(
            cursor,
            candidate["case_id"],
            candidate["chunk_index"]
        )


        output.append({

            "rank":
                len(output) + 1,

            "chunk_id":
                candidate["chunk_id"],

            "case_id":
                candidate["case_id"],

            "filename":
                candidate["filename"],

            "year":
                candidate["year"],

            "chunk_index":
                candidate["chunk_index"],

            "embedding_distance":
                candidate["embedding_distance"],

            "reranker_score":
                candidate["reranker_score"],

            # Actual matched chunk
            "matched_chunk":
                candidate["matched_chunk"],

            # IMPORTANT:
            # RAG expects this key.
            # It contains the actual matched chunk,
            # NOT the entire judgment.
            "document":
                candidate["matched_chunk"],

            # Neighboring context for RAG
            "context":
                full_context,

            "content_hash":
                candidate["content_hash"]
        })


    return output


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("LEGAL INTELLIGENCE SEARCH")
    print("=" * 70)

    print()

    print(
        f"Embedding model : "
        f"{EMBEDDING_MODEL}"
    )

    print(
        f"Reranker        : "
        f"{RERANKER_MODEL}"
    )

    print(
        f"Retrieval       : "
        f"Top {RETRIEVAL_K}"
    )

    print(
        f"Final results   : "
        f"Top {DISPLAY_RESULTS}"
    )

    print()

    print("Type a legal question.")
    print("Type 'exit' to stop.")

    print()


    while True:

        query = input(
            "Query: "
        ).strip()


        # ------------------------------------------------
        # EXIT
        # ------------------------------------------------

        if query.lower() == "exit":
            break


        # ------------------------------------------------
        # EMPTY QUERY
        # ------------------------------------------------

        if not query:
            continue


        # ------------------------------------------------
        # SEARCH
        # ------------------------------------------------

        results = search(
            query
        )


        # ------------------------------------------------
        # DISPLAY
        # ------------------------------------------------

        print()

        print("=" * 70)
        print("RERANKED SEARCH RESULTS")
        print("=" * 70)


        if not results:

            print()
            print("No results found.")
            print()

            continue


        for result in results:

            print()

            print("-" * 70)

            print(
                f"#{result['rank']}  "
                f"Case ID: {result['case_id']}  "
                f"Year: {result['year']}"
            )

            print(
                f"Reranker score: "
                f"{result['reranker_score']:.4f}"
            )

            print(
                f"Embedding distance: "
                f"{result['embedding_distance']:.4f}"
            )

            print(
                f"Matched chunk: "
                f"{result['chunk_index']}"
            )

            print(
                f"File: "
                f"{result['filename']}"
            )

            print()

            # Display ONLY the actual matched chunk
            print(
                result["matched_chunk"]
            )

        print()