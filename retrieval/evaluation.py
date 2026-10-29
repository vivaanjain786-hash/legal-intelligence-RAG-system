import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.search import search


# ============================================================
# GOLD-STANDARD EVALUATION SET
# ============================================================
#
# expected_case_ids should contain cases that are considered
# relevant to the query.
#
# Start with cases we have already verified from our retrieval
# results. We will expand this set carefully.
#
# ============================================================

EVALUATION_SET = [

    {
        "query": "What is personal liberty under Article 21?",
        "expected_case_ids": [
            7409,      # ADM Jabalpur / Shivakant Shukla
            20593,     # Siddharam Satlingappa Mhetre
            1,         # A.K. Gopalan
            8373,      # Maneka Gandhi
            23235,     # Puttaswamy
        ],
    },

]


# ============================================================
# METRICS
# ============================================================

def precision_at_k(retrieved_ids, relevant_ids, k):
    """
    Precision@K =
    relevant results in top K / K
    """

    top_k = retrieved_ids[:k]

    if not top_k:
        return 0.0

    relevant_retrieved = sum(
        1 for case_id in top_k
        if case_id in relevant_ids
    )

    return relevant_retrieved / len(top_k)


def recall_at_k(retrieved_ids, relevant_ids, k):
    """
    Recall@K =
    relevant results in top K / total relevant cases
    """

    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]

    relevant_retrieved = sum(
        1 for case_id in top_k
        if case_id in relevant_ids
    )

    return relevant_retrieved / len(relevant_ids)


def reciprocal_rank(retrieved_ids, relevant_ids):
    """
    Reciprocal Rank =
    1 / rank of first relevant result

    Returns 0 if no relevant result is retrieved.
    """

    for rank, case_id in enumerate(retrieved_ids, start=1):

        if case_id in relevant_ids:
            return 1 / rank

    return 0.0


# ============================================================
# EVALUATE ONE QUERY
# ============================================================

def evaluate_query(query, expected_case_ids):

    print("=" * 80)
    print("QUERY")
    print(query)
    print("=" * 80)

    results = search(query)

    retrieved_ids = [
        result["case_id"]
        for result in results
    ]

    relevant_ids = set(expected_case_ids)

    print()
    print("RETRIEVED CASE IDs:")
    print(retrieved_ids)

    print()
    print("EXPECTED RELEVANT CASE IDs:")
    print(expected_case_ids)

    print()

    for k in [1, 3, 5, 8]:

        precision = precision_at_k(
            retrieved_ids,
            relevant_ids,
            k
        )

        recall = recall_at_k(
            retrieved_ids,
            relevant_ids,
            k
        )

        print(
            f"@{k:<2} "
            f"Precision: {precision:.3f} | "
            f"Recall: {recall:.3f}"
        )

    mrr = reciprocal_rank(
        retrieved_ids,
        relevant_ids
    )

    print()
    print(f"MRR: {mrr:.3f}")

    print()
    print("RANKED RESULTS:")

    for rank, result in enumerate(results, start=1):

        case_id = result["case_id"]

        marker = (
            "✓ RELEVANT"
            if case_id in relevant_ids
            else "  "
        )

        print(
            f"{rank}. "
            f"Case {case_id} "
            f"{marker}"
        )

        print(
            f"   {result['filename']}"
        )

        print(
            f"   Reranker: "
            f"{result['reranker_score']:.4f}"
        )

        print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("LEGAL INTELLIGENCE SYSTEM")
    print("RETRIEVAL EVALUATION")
    print("=" * 80)
    print()

    for item in EVALUATION_SET:

        evaluate_query(
            item["query"],
            item["expected_case_ids"]
        )

    print("=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()