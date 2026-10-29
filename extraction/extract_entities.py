import sqlite3
import re
from pathlib import Path
from collections import Counter
from tqdm import tqdm


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


# ============================================================
# SETTINGS
# ============================================================

# Keep this at 100 until the extraction quality is verified.
TEST_LIMIT = 26622


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_entity(text):
    """
    Normalize extracted legal entity text.

    Used for consistent storage and duplicate detection.
    """

    text = text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = re.sub(
        r"\s*,\s*",
        ", ",
        text
    )

    text = re.sub(
        r"\s*\(\s*",
        "(",
        text
    )

    text = re.sub(
        r"\s*\)",
        ")",
        text
    )

    return text.strip()


# ============================================================
# ARTICLE EXTRACTION
# ============================================================

def extract_articles(text):
    """
    Extract constitutional/legal article references.

    Examples:

        Article 14
        Article 21
        Article 19(1)(a)
        Article 105(2)
        Article 129
    """

    pattern = re.compile(
        r"\bArticle\s+"
        r"\d+"
        r"(?:"
        r"\s*\(\s*\d+[A-Za-z]*\s*\)"
        r")*",
        re.IGNORECASE
    )

    matches = pattern.findall(text)

    entities = []

    for match in matches:

        entity = normalize_entity(match)

        if entity:
            entities.append(entity)

    return entities


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(text):
    """
    Extract statutory section references.

    Examples:

        Section 302
        Section 420
        Section 13(1)
        Section 14A
    """

    pattern = re.compile(
        r"\bSection\s+"
        r"\d+[A-Za-z]*"
        r"(?:"
        r"\s*\(\s*[A-Za-z0-9]+\s*\)"
        r")*",
        re.IGNORECASE
    )

    matches = pattern.findall(text)

    entities = []

    for match in matches:

        entity = normalize_entity(match)

        if entity:
            entities.append(entity)

    return entities


# ============================================================
# RULE EXTRACTION
# ============================================================

def extract_rules(text):
    """
    Extract rule references.

    Examples:

        Rule 5
        Rule 8(2)
        Rule 58
    """

    pattern = re.compile(
        r"\bRule\s+"
        r"\d+[A-Za-z]*"
        r"(?:"
        r"\s*\(\s*[A-Za-z0-9]+\s*\)"
        r")*",
        re.IGNORECASE
    )

    matches = pattern.findall(text)

    entities = []

    for match in matches:

        entity = normalize_entity(match)

        if entity:
            entities.append(entity)

    return entities


# ============================================================
# ACT EXTRACTION
# ============================================================
def extract_acts(text):
    """
    Extract named Acts and major statutory codes.

    The extractor is intentionally conservative.

    Examples:

        Evidence Act
        Income-tax Act, 1922
        Companies Act, 1956
        Government of India Act, 1935
        Bombay Public Security Measures Act
        Code of Civil Procedure
        Code of Criminal Procedure
        Indian Penal Code

    Generic references such as:

        The Act
        this Act
        said Act
        such Act
        of the Act
        in the Act

    are excluded.
    """

    patterns = [

        # ----------------------------------------------------
        # Named Acts
        #
        # Require the actual name to begin with a capitalized
        # word. Connector words are allowed inside the name.
        # ----------------------------------------------------

        re.compile(
            r"\b"
            r"[A-Z][A-Za-z&.\-']*"
            r"(?:"
            r"\s+"
            r"(?:"
            r"[A-Z][A-Za-z&.\-']*"
            r"|of|the|and|for|in|on"
            r")"
            r"){0,8}"
            r"\s+Act"
            r"(?:\s*,?\s*\d{4})?"
            r"\b"
        ),

        # ----------------------------------------------------
        # Code of Civil Procedure
        # ----------------------------------------------------

        re.compile(
            r"\bCode\s+of\s+Civil\s+Procedure"
            r"(?:\s*,?\s*\d{4})?"
            r"\b",
            re.IGNORECASE
        ),

        # ----------------------------------------------------
        # Code of Criminal Procedure
        # ----------------------------------------------------

        re.compile(
            r"\bCode\s+of\s+Criminal\s+Procedure"
            r"(?:\s*,?\s*\d{4})?"
            r"\b",
            re.IGNORECASE
        ),

        # ----------------------------------------------------
        # Indian Penal Code
        # ----------------------------------------------------

        re.compile(
            r"\bIndian\s+Penal\s+Code"
            r"(?:\s*,?\s*\d{4})?"
            r"\b",
            re.IGNORECASE
        ),
    ]

    generic_acts = {
        "the act",
        "this act",
        "that act",
        "said act",
        "such act",
        "an act",
        "of the act",
        "in the act",
        "of act",
    }

    entities = []

    for pattern in patterns:

        matches = pattern.findall(text)

        for match in matches:

            entity = normalize_entity(match)

            if not entity:
                continue

            # -----------------------------------------------
            # Remove generic references
            # -----------------------------------------------

            if entity.lower() in generic_acts:
                continue

            # -----------------------------------------------
            # Remove entities that begin with a connector.
            #
            # Example:
            # "of the Government of India Act, 1935"
            #
            # We want:
            # "Government of India Act, 1935"
            # -----------------------------------------------

            entity = re.sub(
                r"^(?:of|in|on|for|and|the)\s+",
                "",
                entity,
                flags=re.IGNORECASE
            )

            entity = normalize_entity(entity)

            if not entity:
                continue

            # -----------------------------------------------
            # Final generic check
            # -----------------------------------------------

            if entity.lower() in generic_acts:
                continue

            # -----------------------------------------------
            # An actual Act should contain "Act"
            # -----------------------------------------------

            if not re.search(
                r"\bAct\b",
                entity,
                re.IGNORECASE
            ):
                continue

            entities.append(entity)

    return entities


# ============================================================
# CONSTITUTION EXTRACTION
# ============================================================

def extract_constitutions(text):
    """
    Extract constitutional instrument references.

    Example:

        Constitution of India
    """

    pattern = re.compile(
        r"\bConstitution\s+of\s+India\b",
        re.IGNORECASE
    )

    matches = pattern.findall(text)

    entities = []

    for match in matches:

        entity = normalize_entity(match)

        if entity:
            entities.append(entity)

    return entities


# ============================================================
# DEDUPLICATION
# ============================================================

def unique_entities(entities):
    """
    Remove duplicate entities within a case.
    """

    seen = set()
    result = []

    for entity in entities:

        normalized = entity.lower()

        if normalized in seen:
            continue

        seen.add(normalized)

        result.append(entity)

    return result


# ============================================================
# DATABASE CHECK
# ============================================================

if not DB_PATH.exists():

    raise FileNotFoundError(
        f"Database not found:\n{DB_PATH}"
    )


conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()


# ============================================================
# CHECK ENTITY TABLE
# ============================================================

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name = 'case_entities'
""")

if cursor.fetchone() is None:

    conn.close()

    raise RuntimeError(
        "case_entities table does not exist.\n"
        "Run create_entity_table.py first."
    )


# ============================================================
# LOAD TEST CASES
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
print("LEGAL INTELLIGENCE SYSTEM - ENTITY EXTRACTION")
print("=" * 70)

print(f"Database       : {DB_PATH}")
print(f"Test cases     : {len(cases)}")
print()


# ============================================================
# STATISTICS
# ============================================================

entity_counts = Counter()

cases_with_entities = 0
total_entities = 0
failed_cases = 0


# ============================================================
# PROCESS CASES
# ============================================================

for case_id, filename, text in tqdm(
    cases,
    desc="Extracting entities"
):

    try:

        # ----------------------------------------------------
        # Extract entities
        # ----------------------------------------------------

        acts = unique_entities(
            extract_acts(text)
        )

        constitutions = unique_entities(
            extract_constitutions(text)
        )

        articles = unique_entities(
            extract_articles(text)
        )

        sections = unique_entities(
            extract_sections(text)
        )

        rules = unique_entities(
            extract_rules(text)
        )


        # ----------------------------------------------------
        # Combine entities
        # ----------------------------------------------------

        all_entities = []

        for entity in acts:

            all_entities.append(
                ("ACT", entity)
            )

        for entity in constitutions:

            all_entities.append(
                ("CONSTITUTION", entity)
            )

        for entity in articles:

            all_entities.append(
                ("ARTICLE", entity)
            )

        for entity in sections:

            all_entities.append(
                ("SECTION", entity)
            )

        for entity in rules:

            all_entities.append(
                ("RULE", entity)
            )


        if all_entities:

            cases_with_entities += 1


        # ----------------------------------------------------
        # Insert entities
        # ----------------------------------------------------

        for entity_type, entity_text in all_entities:

            normalized = normalize_entity(
                entity_text
            )

            cursor.execute("""
                INSERT OR IGNORE INTO case_entities (
                    case_id,
                    entity_type,
                    entity_text,
                    normalized_text
                )
                VALUES (?, ?, ?, ?)
            """, (
                case_id,
                entity_type,
                entity_text,
                normalized
            ))

            entity_counts[entity_type] += 1
            total_entities += 1


    except Exception as e:

        failed_cases += 1

        print()
        print("-" * 70)
        print("ERROR")
        print(f"Case ID : {case_id}")
        print(f"File    : {filename}")
        print(f"Error   : {e}")
        print("-" * 70)


# ============================================================
# COMMIT
# ============================================================

conn.commit()


# ============================================================
# DATABASE COUNTS
# ============================================================

cursor.execute("""
    SELECT COUNT(*)
    FROM case_entities
""")

database_total = cursor.fetchone()[0]


cursor.execute("""
    SELECT
        entity_type,
        COUNT(*)
    FROM case_entities
    GROUP BY entity_type
    ORDER BY entity_type
""")

database_counts = cursor.fetchall()


conn.close()


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 70)
print("ENTITY EXTRACTION TEST COMPLETE")
print("=" * 70)

print(f"Cases processed       : {len(cases):,}")
print(f"Cases with entities   : {cases_with_entities:,}")
print(f"Entities extracted    : {total_entities:,}")
print(f"Failed cases          : {failed_cases:,}")

print()
print("EXTRACTED THIS RUN")
print("-" * 40)

for entity_type, count in entity_counts.items():

    print(
        f"{entity_type:18} : {count:,}"
    )


print()
print("DATABASE TOTAL")
print("-" * 40)

for entity_type, count in database_counts:

    print(
        f"{entity_type:18} : {count:,}"
    )


print()
print(
    f"Total database entities: "
    f"{database_total:,}"
)

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)