from search import search
from citations import add_citations


# ============================================================
# TEST QUERY
# ============================================================

QUERY = "What is personal liberty under Article 21?"


# ============================================================
# SEARCH
# ============================================================

print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - SEARCH + CITATION TEST")
print("=" * 70)
print()

print(f"Query: {QUERY}")
print()

results = search(QUERY)


# ============================================================
# ADD CITATIONS
# ============================================================

results = add_citations(results)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 70)
print("RESULTS WITH SOURCES")
print("=" * 70)

for result in results:

    source = result["source"]

    print()
    print("-" * 70)

    print(
        f"#{result['rank']} "
        f"| Case ID: {result['case_id']} "
        f"| Chunk: {result['chunk_index']}"
    )

    print()
    print("SOURCE:")
    print(source["source_label"])

    print()
    print("CASE:")
    print(source["title"])

    print()
    print("DATE:")
    print(source["decision_date"])

    print()
    print("COURT:")
    print(source["court"])

    print()
    print("JUDGE:")
    print(source["judge"])

    print()
    print("CITATION:")
    print(source["citation"])

    print()
    print("MATCHED PASSAGE:")
    print(source["text"])


print()
print("=" * 70)
print("SEARCH + CITATION TEST COMPLETE")
print("=" * 70)