from .database import get_connection


def get_overview():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS count FROM cases")
    total_cases = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM metadata
    """)
    metadata_cases = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM case_entities
    """)
    total_entities = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM chunks
    """)
    total_chunks = cursor.fetchone()["count"]

    conn.close()

    return {
        "total_cases": total_cases,
        "metadata_cases": metadata_cases,
        "total_entities": total_entities,
        "total_chunks": total_chunks,
    }


def get_cases_by_year():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            year,
            COUNT(*) AS count
        FROM cases
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "year": row["year"],
            "count": row["count"]
        }
        for row in rows
    ]


def get_parser_distribution():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            format,
            COUNT(*) AS count
        FROM metadata
        GROUP BY format
        ORDER BY count DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "format": row["format"],
            "count": row["count"]
        }
        for row in rows
    ]


def get_entity_distribution():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            entity_type,
            COUNT(*) AS count
        FROM case_entities
        GROUP BY entity_type
        ORDER BY count DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "entity_type": row["entity_type"],
            "count": row["count"]
        }
        for row in rows
    ]


def get_top_judges(limit=20):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            judge,
            COUNT(*) AS count
        FROM metadata
        WHERE judge IS NOT NULL
          AND TRIM(judge) != ''
        GROUP BY judge
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "judge": row["judge"],
            "count": row["count"]
        }
        for row in rows
    ]


# ============================================================
# JUDGMENTS — BROWSE
# ============================================================

def get_cases(
    page=1,
    page_size=20,
    year_from=None,
    year_to=None,
    case_type=None,
    q=None,
):

    conn = get_connection()
    cursor = conn.cursor()

    where = ["1=1"]
    params = []

    if year_from is not None:
        where.append("c.year >= ?")
        params.append(year_from)

    if year_to is not None:
        where.append("c.year <= ?")
        params.append(year_to)

    if case_type:
        where.append("LOWER(TRIM(m.case_type)) = LOWER(TRIM(?))")
        params.append(case_type)

    if q:
        where.append("""(
            m.title LIKE ?
            OR m.petitioner LIKE ?
            OR m.respondent LIKE ?
        )""")
        like = f"%{q}%"
        params.extend([like, like, like])

    where_sql = " AND ".join(where)

    cursor.execute(f"""
        SELECT COUNT(*) AS count
        FROM cases c
        LEFT JOIN metadata m ON m.case_id = c.id
        WHERE {where_sql}
    """, params)

    total = cursor.fetchone()["count"]

    offset = (page - 1) * page_size

    cursor.execute(f"""
        SELECT
            c.id AS case_id,
            c.year,
            m.title,
            m.decision_date,
            m.citation,
            m.case_type,
            m.judge,
            m.petitioner,
            m.respondent
        FROM cases c
        LEFT JOIN metadata m ON m.case_id = c.id
        WHERE {where_sql}
        ORDER BY c.year DESC, c.id ASC
        LIMIT ? OFFSET ?
    """, params + [page_size, offset])

    rows = cursor.fetchall()

    conn.close()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [dict(row) for row in rows],
    }


def get_case_detail(case_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id AS case_id,
            c.filename,
            c.year,
            c.pages,
            c.word_count,
            c.clean_text,
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
            m.respondent,
            m.reportable,
            m.format
        FROM cases c
        LEFT JOIN metadata m ON m.case_id = c.id
        WHERE c.id = ?
    """, (case_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    case = dict(row)

    excerpt = (case.pop("clean_text", None) or "")[:3000].strip()
    case["text_excerpt"] = excerpt

    cursor.execute("""
        SELECT
            entity_type,
            normalized_text,
            COUNT(*) AS count
        FROM case_entities
        WHERE case_id = ?
        GROUP BY entity_type, normalized_text
        ORDER BY count DESC
    """, (case_id,))

    entities = {}

    for erow in cursor.fetchall():
        entities.setdefault(erow["entity_type"], []).append({
            "value": erow["normalized_text"],
            "count": erow["count"],
        })

    case["entities"] = entities

    conn.close()

    return case


def get_case_types(limit=25):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            MAX(case_type) AS label,
            COUNT(*) AS count
        FROM metadata
        WHERE case_type IS NOT NULL
          AND TRIM(case_type) != ''
        GROUP BY LOWER(TRIM(case_type))
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ============================================================
# ENTITIES — BROWSE
# ============================================================

def get_top_entities(entity_type, limit=25):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            normalized_text,
            COUNT(*) AS count,
            COUNT(DISTINCT case_id) AS case_count
        FROM case_entities
        WHERE entity_type = ?
        GROUP BY normalized_text
        ORDER BY count DESC
        LIMIT ?
    """, (entity_type, limit))

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_cases_for_entity(entity_type, value, limit=20):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            c.id AS case_id,
            c.year,
            m.title,
            m.citation,
            m.judge
        FROM case_entities e
        JOIN cases c ON c.id = e.case_id
        LEFT JOIN metadata m ON m.case_id = c.id
        WHERE e.entity_type = ?
          AND e.normalized_text = ?
        ORDER BY c.year DESC
        LIMIT ?
    """, (entity_type, value, limit))

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ============================================================
# ANALYTICS
# ============================================================

def get_case_type_distribution(limit=10):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            MAX(case_type) AS case_type,
            COUNT(*) AS count
        FROM metadata
        WHERE case_type IS NOT NULL
          AND TRIM(case_type) != ''
        GROUP BY LOWER(TRIM(case_type))
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_reportable_distribution():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(NULLIF(TRIM(reportable), ''), 'Unknown') AS reportable,
            COUNT(*) AS count
        FROM metadata
        GROUP BY reportable
        ORDER BY count DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_metadata_completeness():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS count FROM metadata")
    total = cursor.fetchone()["count"] or 1

    fields = [
        "citation",
        "case_type",
        "case_number",
        "author",
        "bench",
        "judge",
        "petitioner",
        "respondent",
        "acts",
        "articles",
    ]

    completeness = []

    for field in fields:
        cursor.execute(f"""
            SELECT COUNT(*) AS count
            FROM metadata
            WHERE {field} IS NOT NULL
              AND TRIM({field}) != ''
        """)

        filled = cursor.fetchone()["count"]

        completeness.append({
            "field": field,
            "filled": filled,
            "total": total,
            "percent": round((filled / total) * 100, 1),
        })

    conn.close()

    return completeness