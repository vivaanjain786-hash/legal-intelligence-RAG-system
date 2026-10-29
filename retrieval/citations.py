import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


# ============================================================
# GET CASE METADATA
# ============================================================

def get_case_metadata(case_id):
    """
    Retrieve legal metadata for a case.

    Returns a dictionary containing the information
    needed to construct a human-readable source citation.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                m.case_id,
                m.title,
                m.decision_date,
                m.court,
                m.citation,
                m.case_type,
                m.case_number,
                m.author,
                m.bench,
                m.judge,
                m.petitioner,
                m.respondent
            FROM metadata m
            WHERE m.case_id = ?
            LIMIT 1
            """,
            (case_id,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "case_id": row[0],
            "title": row[1],
            "decision_date": row[2],
            "court": row[3],
            "citation": row[4],
            "case_type": row[5],
            "case_number": row[6],
            "author": row[7],
            "bench": row[8],
            "judge": row[9],
            "petitioner": row[10],
            "respondent": row[11],
        }

    finally:
        conn.close()


# ============================================================
# FORMAT SOURCE CITATION
# ============================================================

def format_citation(metadata, chunk_index=None):
    """
    Convert case metadata into a compact human-readable
    source citation.
    """

    if not metadata:
        return "Unknown source"

    title = metadata.get("title") or "Unknown Case"

    year = ""

    decision_date = metadata.get("decision_date")

    if decision_date:
        year = str(decision_date)[-4:]

    citation = metadata.get("citation")

    parts = []

    # --------------------------------------------------------
    # Case title
    # --------------------------------------------------------

    parts.append(title.strip())

    # --------------------------------------------------------
    # Official citation
    # --------------------------------------------------------

    if citation:
        citation = citation.strip()

        if citation not in parts:
            parts.append(citation)

    # --------------------------------------------------------
    # Year fallback
    # --------------------------------------------------------

    elif year:
        parts.append(year)

    # --------------------------------------------------------
    # Chunk reference
    # --------------------------------------------------------

    if chunk_index is not None:
        parts.append(
            f"Chunk {chunk_index}"
        )

    return " | ".join(parts)


# ============================================================
# CREATE SOURCE OBJECT
# ============================================================

def build_source(result):
    """
    Combine retrieval information and database metadata
    into a structured source object.
    """

    case_id = result.get("case_id")

    chunk_index = result.get(
        "chunk_index"
    )

    metadata = get_case_metadata(
        case_id
    )

    # ========================================================
    # FALLBACK
    # ========================================================

    if not metadata:

        title = result.get(
            "filename",
            "Unknown source"
        )

        year = result.get(
            "year",
            ""
        )

        source_label = title

        if year:
            source_label += (
                f" | {year}"
            )

        source_label += (
            f" | Case ID {case_id}"
            f" | Chunk {chunk_index}"
        )

        return {

            "source_id": (
                f"case-{case_id}-"
                f"chunk-{chunk_index}"
            ),

            "case_id": case_id,

            "chunk_index": chunk_index,

            "title": title,

            "year": year,

            "decision_date": None,

            "court": None,

            "citation": None,

            "case_type": None,

            "case_number": None,

            "judge": None,

            "petitioner": None,

            "respondent": None,

            "source_label": source_label,

            "text": result.get(
                "matched_chunk",
                ""
            ),

            "context": result.get(
                "context",
                ""
            ),

            "reranker_score": result.get(
                "reranker_score"
            ),

            "embedding_distance": result.get(
                "embedding_distance"
            ),
        }

    # ========================================================
    # NORMAL METADATA RESULT
    # ========================================================

    return {

        "source_id": (
            f"case-{case_id}-"
            f"chunk-{chunk_index}"
        ),

        "case_id": case_id,

        "chunk_index": chunk_index,

        "title": metadata["title"],

        "year": result.get(
            "year",
            ""
        ),

        "decision_date": metadata[
            "decision_date"
        ],

        "court": metadata[
            "court"
        ],

        "citation": metadata[
            "citation"
        ],

        "case_type": metadata[
            "case_type"
        ],

        "case_number": metadata[
            "case_number"
        ],

        "judge": metadata[
            "judge"
        ],

        "petitioner": metadata[
            "petitioner"
        ],

        "respondent": metadata[
            "respondent"
        ],

        "source_label": format_citation(
            metadata,
            chunk_index
        ),

        "text": result.get(
            "matched_chunk",
            ""
        ),

        "context": result.get(
            "context",
            ""
        ),

        "reranker_score": result.get(
            "reranker_score"
        ),

        "embedding_distance": result.get(
            "embedding_distance"
        ),
    }


# ============================================================
# ENRICH SEARCH RESULTS
# ============================================================

def add_citations(results):
    """
    Add structured citation information to all
    retrieved search results.
    """

    enriched_results = []

    for result in results:

        source = build_source(
            result
        )

        enriched_result = dict(
            result
        )

        enriched_result["source"] = source

        enriched_results.append(
            enriched_result
        )

    return enriched_results