import os
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
# from google import genai


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

# Gemini API key setup (kept for an easy provider rollback):
# API_KEY = os.getenv(
#     "GEMINI_API_KEY"
# )

# if not API_KEY:
#     raise ValueError(
#         "GEMINI_API_KEY not found.\n"
#         "Make sure it is present in the .env file."
#     )

# ============================================================
# GEMINI (kept for an easy provider rollback)
# ============================================================

# client = genai.Client(
#     api_key=API_KEY
# )

# MODEL_NAME = "gemini-3.5-flash"


# ============================================================
# OPENROUTER
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL_NAME = os.getenv("OPENROUTER_MODEL", "openrouter/free")


# ============================================================
# RETRIEVAL
# ============================================================

from retrieval.search import search


# ============================================================
# RAG ANSWER GENERATION
# ============================================================

def generate_answer(query):
    results = search(query)

    if not results:
        return "No relevant legal authorities were retrieved."

    return generate_answer_from_results(query, results)


def generate_answer_from_results(query, results):
    """
    Generate a grounded answer using local retrieved passages and OpenRouter.
    """

    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not found. Add your OpenRouter API key to .env."
        )

    context_parts = []
    for i, result in enumerate(results, start=1):
        passage = result.get("document") or result.get("matched_chunk", "")
        context_parts.append(
            f"""SOURCE {i}
Case Name/File: {result.get('filename', 'Unknown')}
Year: {result.get('year', 'Unknown')}
Case ID: {result.get('case_id', 'Unknown')}
LEGAL PASSAGE:
{passage}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are a legal research assistant for an Indian Supreme
Court judgment retrieval system.

Answer the user's question using ONLY the retrieved legal
material below.

IMPORTANT RULES:

1. Do not invent cases, statutes, constitutional provisions,
   legal principles, facts, dates, or citations.

2. Do not rely on outside knowledge when the retrieved
   material does not support a claim.

3. If the retrieved material is insufficient, clearly state:
   "The retrieved material is insufficient to answer this
   question."

4. Distinguish between what the retrieved cases actually
   state and any explanation you provide.

5. Mention the relevant case name/file and year when using
   an important legal proposition.

6. Do not provide personal legal advice. 

7. Do not claim that a case establishes a proposition unless
   that proposition is supported by the retrieved passage.

8. Keep the answer focused on the user's question.

9. Write the answer as normal prose in one or two paragraphs.
   Do not use Markdown, headings, bullet points, numbered lists,
   bold, italics, asterisks, or hashtags.

USER QUESTION:
{query}

RETRIEVED LEGAL MATERIAL:
{context}
"""

    print(f"Calling OpenRouter ({OPENROUTER_MODEL_NAME})...")
    request_body = json.dumps({
        "model": OPENROUTER_MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }).encode("utf-8")

    request = Request(
        OPENROUTER_API_URL,
        data=request_body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            completion = json.load(response)
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenRouter API returned HTTP {error.code}: {details}"
        ) from error

    try:
        answer = completion["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            "OpenRouter returned an unexpected response format."
        ) from error

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("OpenRouter returned an empty answer.")

    answer = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", answer)
    answer = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+", "", answer)
    answer = re.sub(r"(?<!\w)(\*{1,2}|_{1,2})(.+?)\1(?!\w)", r"\2", answer)
    answer = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", answer)
    return re.sub(r"\s+", " ", answer).strip()



# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("LEGAL INTELLIGENCE SYSTEM - RAG")
    print("=" * 70)

    print()

    print(f"Provider: OpenRouter ({OPENROUTER_MODEL_NAME})")

    print()

    print("Ask a legal question.")
    print("Type 'exit' to stop.")

    print()


    while True:

        query = input(
            "Question: "
        ).strip()


        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if query.lower() == "exit":
            break


        # ----------------------------------------------------
        # EMPTY QUERY
        # ----------------------------------------------------

        if not query:
            continue


        print()
        print("Generating answer...")
        print()


        try:

            answer = generate_answer(query)

            print("=" * 70)
            print("ANSWER")
            print("=" * 70)

            print()

            print(answer)

            print()

        except Exception as e:

            print()
            print("ERROR:")
            print(e)
            print()