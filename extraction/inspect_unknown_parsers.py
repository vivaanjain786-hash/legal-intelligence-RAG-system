import re
import sys
import zipfile
from pathlib import Path

import pymupdf as fitz


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")
ZIP_PATH = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset.zip")

# Allow imports from project root
sys.path.insert(0, str(BASE_DIR))

from parser.parser_factory import ParserFactory


# ============================================================
# SETTINGS
# ============================================================

HEADER_LINES = 100


# ============================================================
# YEAR EXTRACTION
# ============================================================

def get_year(filename):
    match = re.search(
        r"(?:^|/)(19|20)\d{2}(?:/|$)",
        filename
    )

    if match:
        year_match = re.search(
            r"(19|20)\d{2}",
            match.group(0)
        )

        if year_match:
            return int(year_match.group(0))

    return None


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text(pdf_bytes):

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    text = "\n".join(
        page.get_text("text")
        for page in document
    )

    document.close()

    return text


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LEGAL INTELLIGENCE SYSTEM - UNKNOWN PARSER DIAGNOSTIC")
    print("=" * 70)
    print(f"ZIP: {ZIP_PATH}")
    print()

    if not ZIP_PATH.exists():
        raise FileNotFoundError(
            f"ZIP not found: {ZIP_PATH}"
        )

    factory = ParserFactory()

    with zipfile.ZipFile(
        ZIP_PATH,
        "r"
    ) as zip_file:

        pdf_files = [
            name
            for name in zip_file.namelist()
            if name.lower().endswith(".pdf")
        ]

        print(
            f"Total PDFs in ZIP: {len(pdf_files):,}"
        )

        print()
        print("Searching for UNKNOWN parser cases...")
        print()

        unknown_cases = []

        for filename in pdf_files:

            try:

                with zip_file.open(
                    filename
                ) as pdf_file:

                    pdf_bytes = pdf_file.read()

                text = extract_text(
                    pdf_bytes
                )

                parser = factory.get_parser(
                    text
                )

                if parser is None:

                    year = get_year(filename)

                    unknown_cases.append(
                        (
                            year,
                            filename,
                            text
                        )
                    )

            except Exception as exc:

                print(
                    f"ERROR processing {filename}: {exc}"
                )

        unknown_cases.sort(
            key=lambda x: (
                x[0] if x[0] is not None else 9999,
                x[1]
            )
        )

        print(
            f"UNKNOWN cases found: {len(unknown_cases)}"
        )

        print()
        print("=" * 70)
        print("UNKNOWN CASE DETAILS")
        print("=" * 70)

        for index, (
            year,
            filename,
            text
        ) in enumerate(
            unknown_cases,
            start=1
        ):

            print()
            print()
            print("#" * 70)
            print(
                f"UNKNOWN CASE {index}/{len(unknown_cases)}"
            )
            print("#" * 70)

            print(
                f"YEAR     : {year}"
            )

            print(
                f"FILE     : {Path(filename).name}"
            )

            print(
                f"TEXT LEN : {len(text):,} characters"
            )

            print()
            print("-" * 70)
            print(
                f"FIRST {HEADER_LINES} LINES OF EXTRACTED TEXT"
            )
            print("-" * 70)

            lines = text.splitlines()

            for line_number, line in enumerate(
                lines[:HEADER_LINES],
                start=1
            ):

                print(
                    f"{line_number:03d}: {line}"
                )

            print()
            print("-" * 70)
            print("POSSIBLE FORMAT MARKERS")
            print("-" * 70)

            markers = [
                "SUPREME COURT",
                "JUDGMENT",
                "ORDER",
                "BENCH",
                "PETITIONER",
                "RESPONDENT",
                "CASE NO",
                "CITATION",
                "REPORTABLE",
                "ACT",
                "ARTICLE",
                "VERSUS",
                "APPELLANT",
                "RESPONDENT",
            ]

            upper_text = text.upper()

            for marker in markers:

                if marker in upper_text:
                    print(
                        f"FOUND : {marker}"
                    )

            print()
            print("=" * 70)

    print()
    print("DIAGNOSTIC COMPLETE")
    print()
    print("IMPORTANT:")
    print("• No SQLite database was modified.")
    print("• Original ZIP was not modified.")
    print("• Existing parser files were not modified.")


if __name__ == "__main__":
    main()