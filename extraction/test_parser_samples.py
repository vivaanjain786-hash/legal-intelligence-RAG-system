import sys
import zipfile
import re
import unicodedata
from pathlib import Path

import pymupdf as fitz
from tqdm import tqdm


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")
ZIP_PATH = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset.zip")

PROJECT_ROOT = BASE_DIR
sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory


SAMPLES_PER_YEAR = 5
TARGET_YEARS = [1950, 2000, 2025]


# ============================================================
# YEAR EXTRACTION
# ============================================================

def extract_year(filename):
    parts = Path(filename).parts

    for part in parts:
        if re.fullmatch(r"(19|20)\d{2}", part):
            return int(part)

    match = re.search(r"\b(19|20)\d{2}\b", filename)

    if match:
        return int(match.group())

    return None


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(pdf_bytes):
    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    text_parts = []

    for page in document:
        text_parts.append(
            page.get_text("text")
        )

    text = "\n".join(text_parts)

    pages = len(document)

    document.close()

    return text, pages


# ============================================================
# TEXT CLEANING
# IMPORTANT:
# This intentionally matches clean_text.py
# while preserving line breaks.
# ============================================================

def clean_text(text):

    if not text:
        return ""

    # Unicode normalization
    text = unicodedata.normalize(
        "NFKC",
        text
    )

    # Remove URLs
    text = re.sub(
        r"https?://\S+",
        "",
        text
    )

    # Replace tabs with spaces
    text = text.replace(
        "\t",
        " "
    )

    # Remove control characters
    text = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F]",
        "",
        text
    )

    # Collapse repeated spaces
    # IMPORTANT: does NOT remove newlines
    text = re.sub(
        r"[ ]{2,}",
        " ",
        text
    )

    # Reduce excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


# ============================================================
# SAMPLE SELECTION
# ============================================================

def select_samples(pdf_files):

    selected = []

    for year in TARGET_YEARS:

        year_files = [
            pdf
            for pdf in pdf_files
            if extract_year(pdf) == year
        ]

        year_files.sort()

        samples = year_files[
            :SAMPLES_PER_YEAR
        ]

        selected.extend(samples)

    return selected


# ============================================================
# METADATA DISPLAY
# ============================================================

def print_metadata(metadata):

    for key, value in metadata.items():

        print(
            f"{key:15}: {value}"
        )


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("LEGAL INTELLIGENCE SYSTEM - PARSER SAMPLE TEST")
print("=" * 70)

print(
    f"ZIP: {ZIP_PATH}"
)

print()


# ============================================================
# VALIDATE ZIP
# ============================================================

if not ZIP_PATH.exists():

    raise FileNotFoundError(
        f"ZIP file not found:\n{ZIP_PATH}"
    )


# ============================================================
# INITIALIZE PARSER FACTORY
# ============================================================

factory = ParserFactory()


# ============================================================
# OPEN ZIP
# ============================================================

with zipfile.ZipFile(
    ZIP_PATH,
    "r"
) as zip_file:

    # --------------------------------------------------------
    # Find PDFs
    # --------------------------------------------------------

    pdf_files = [
        name
        for name in zip_file.namelist()
        if name.lower().endswith(".pdf")
    ]

    print(
        f"Total PDFs in ZIP: {len(pdf_files):,}"
    )

    if not pdf_files:

        raise RuntimeError(
            "No PDF files found in ZIP."
        )


    # --------------------------------------------------------
    # Select samples
    # --------------------------------------------------------

    samples = select_samples(
        pdf_files
    )

    print()

    print(
        f"Selected samples: {len(samples)}"
    )

    print(
        f"Years tested: "
        f"{', '.join(map(str, TARGET_YEARS))}"
    )

    print(
        f"Samples per year: "
        f"{SAMPLES_PER_YEAR}"
    )

    print()


    # ========================================================
    # PROCESS EACH SAMPLE
    # ========================================================

    for index, pdf_name in enumerate(
        samples,
        start=1
    ):

        print()
        print("=" * 70)

        print(
            f"SAMPLE {index}/{len(samples)}"
        )

        print("=" * 70)

        print(
            f"FILE : {pdf_name}"
        )


        # ----------------------------------------------------
        # Determine year
        # ----------------------------------------------------

        year = extract_year(
            pdf_name
        )

        print(
            f"YEAR : {year}"
        )


        # ----------------------------------------------------
        # Extract PDF
        # ----------------------------------------------------

        try:

            with zip_file.open(
                pdf_name
            ) as pdf_file:

                pdf_bytes = pdf_file.read()


            # ------------------------------------------------
            # Extract text
            # ------------------------------------------------

            text, pages = extract_pdf_text(
                pdf_bytes
            )


            print(
                f"PAGES: {pages:,}"
            )

            print(
                f"WORDS: {len(text.split()):,}"
            )


            # ------------------------------------------------
            # Validate extracted text
            # ------------------------------------------------

            if not text.strip():

                print()
                print(
                    "❌ NO TEXT EXTRACTED"
                )

                continue


            # ------------------------------------------------
            # Clean text
            # ------------------------------------------------

            cleaned = clean_text(
                text
            )


            # ------------------------------------------------
            # Detect parser
            # ------------------------------------------------

            parser = factory.get_parser(
                cleaned
            )


            if parser is None:

                print()
                print(
                    "PARSER: UNKNOWN"
                )

                continue


            # ------------------------------------------------
            # Parse metadata
            # ------------------------------------------------

            print(
                f"PARSER: "
                f"{parser.__class__.__name__}"
            )

            print()

            print(
                "METADATA"
            )

            print(
                "-" * 70
            )


            metadata = parser.parse(
                cleaned
            )


            print_metadata(
                metadata
            )


        # ----------------------------------------------------
        # Error handling
        # ----------------------------------------------------

        except Exception as e:

            print()

            print(
                "❌ ERROR"
            )

            print(
                f"{type(e).__name__}: {e}"
            )


# ============================================================
# COMPLETE
# ============================================================

print()

print("=" * 70)
print("PARSER SAMPLE TEST COMPLETE")
print("=" * 70)

print()

print("IMPORTANT:")

print(
    "• SQLite database was NOT modified."
)

print(
    "• Original ZIP was NOT modified."
)

print(
    "• PDFs were processed only in memory."
)

print()

print(
    "Review the parser outputs above before "
    "proceeding."
)