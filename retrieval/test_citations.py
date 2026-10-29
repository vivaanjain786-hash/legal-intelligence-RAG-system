from citations import get_case_metadata, build_source


# ============================================================
# TEST CASE
# ============================================================

CASE_ID = 7409
CHUNK_INDEX = 74


# ============================================================
# TEST METADATA
# ============================================================

print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - CITATION TEST")
print("=" * 70)
print()

metadata = get_case_metadata(CASE_ID)

if not metadata:
    print("ERROR: No metadata found.")
    raise SystemExit

print("CASE METADATA")
print("-" * 70)

for key, value in metadata.items():
    print(f"{key:15}: {value}")


# ============================================================
# TEST SOURCE OBJECT
# ============================================================

fake_result = {
    "case_id": CASE_ID,
    "chunk_index": CHUNK_INDEX,
    "year": 1976,
    "filename": "test.pdf",
    "matched_chunk": (
        "This is a test retrieved passage from the judgment."
    ),
    "context": (
        "This is surrounding context from the judgment."
    ),
    "reranker_score": 6.3673,
    "embedding_distance": 0.25,
}


source = build_source(fake_result)


print()
print("=" * 70)
print("STRUCTURED SOURCE")
print("=" * 70)
print()

for key, value in source.items():
    print(f"{key:20}: {value}")


print()
print("=" * 70)
print("CITATION TEST COMPLETE")
print("=" * 70)