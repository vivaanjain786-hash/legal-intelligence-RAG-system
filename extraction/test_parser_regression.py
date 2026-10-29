import re
import zipfile
import sys
from pathlib import Path

import pymupdf as fitz


BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")

# Allow imports from the project root
sys.path.insert(0, str(BASE_DIR))

from parser.parser_factory import ParserFactory


BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")
ZIP_PATH = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset.zip")

SAMPLES_PER_PERIOD = 60


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
        return int(year_match.group(0))

    return None


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


def classify_period(year):
    if year is None:
        return None

    if 1950 <= year <= 1970:
        return "1950-1970"

    if 1971 <= year <= 2000:
        return "1971-2000"

    if 2001 <= year <= 2025:
        return "2001-2025"

    return None


def main():

    print("=" * 70)
    print("LEGAL INTELLIGENCE SYSTEM - 180 CASE REGRESSION TEST")
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

        # --------------------------------------------------------
        # Build chronological groups
        # --------------------------------------------------------

        groups = {
            "1950-1970": [],
            "1971-2000": [],
            "2001-2025": [],
        }

        for filename in pdf_files:

            year = get_year(filename)
            period = classify_period(year)

            if period:
                groups[period].append(
                    (year, filename)
                )

        for period in groups:
            groups[period].sort(
                key=lambda x: x[0]
            )

        # --------------------------------------------------------
        # Select evenly distributed samples
        # --------------------------------------------------------

        selected = []

        for period, files in groups.items():

            print(
                f"{period}: {len(files):,} PDFs available"
            )

            if len(files) < SAMPLES_PER_PERIOD:
                raise RuntimeError(
                    f"Not enough files in {period}"
                )

            # Evenly sample across the period.
            step = len(files) / SAMPLES_PER_PERIOD

            indices = [
                min(
                    int(i * step),
                    len(files) - 1
                )
                for i in range(
                    SAMPLES_PER_PERIOD
                )
            ]

            period_samples = [
                files[index]
                for index in indices
            ]

            selected.extend(
                period_samples
            )

            print(
                f"  Selected: {len(period_samples)}"
            )

        print()
        print(
            f"Total selected cases: {len(selected)}"
        )
        print()

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        parser_counts = {}

        field_names = [
            "title",
            "decision_date",
            "court",
            "citation",
            "case_type",
            "case_number",
            "author",
            "bench",
            "judge",
            "petitioner",
            "respondent",
            "reportable",
            "acts",
            "articles",
        ]

        none_counts = {
            field: 0
            for field in field_names
        }

        total_cases = 0
        unknown_parser = 0
        failed_cases = []

        # --------------------------------------------------------
        # Process selected PDFs
        # --------------------------------------------------------

        for index, (year, filename) in enumerate(
            selected,
            start=1
        ):

            print(
                f"[{index:03d}/{len(selected):03d}] "
                f"{year} | {Path(filename).name}"
            )

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

                    unknown_parser += 1

                    print(
                        "       PARSER: UNKNOWN"
                    )

                    continue

                parser_name = (
                    parser.__class__.__name__
                )

                parser_counts[parser_name] = (
                    parser_counts.get(
                        parser_name,
                        0
                    ) + 1
                )

                metadata = parser.parse(
                    text
                )

                total_cases += 1

                for field in field_names:

                    value = metadata.get(
                        field
                    )

                    if (
                        value is None
                        or value == ""
                    ):
                        none_counts[field] += 1

                print(
                    f"       PARSER: {parser_name}"
                )

            except Exception as exc:

                failed_cases.append(
                    (
                        filename,
                        str(exc)
                    )
                )

                print(
                    f"       ERROR: {exc}"
                )

        # --------------------------------------------------------
        # Final report
        # --------------------------------------------------------

        print()
        print("=" * 70)
        print("REGRESSION TEST RESULTS")
        print("=" * 70)

        print()
        print("PARSER DISTRIBUTION")
        print("-" * 70)

        for parser_name, count in sorted(
            parser_counts.items()
        ):

            percentage = (
                count / len(selected) * 100
            )

            print(
                f"{parser_name:25}"
                f"{count:6} "
                f"({percentage:6.2f}%)"
            )

        print(
            f"{'UNKNOWN':25}"
            f"{unknown_parser:6} "
            f"({unknown_parser / len(selected) * 100:6.2f}%)"
        )

        print()
        print("NONE / EMPTY FIELD COUNTS")
        print("-" * 70)

        for field in field_names:

            count = none_counts[field]

            percentage = (
                count / total_cases * 100
                if total_cases
                else 0
            )

            print(
                f"{field:20}"
                f"{count:6} "
                f"({percentage:6.2f}%)"
            )

        print()
        print("FAILED CASES")
        print("-" * 70)

        if failed_cases:

            for filename, error in failed_cases:

                print(
                    f"{Path(filename).name}"
                )
                print(
                    f"  {error}"
                )

        else:

            print("None")

        print()
        print("=" * 70)
        print("REGRESSION TEST COMPLETE")
        print("=" * 70)

        print()
        print("IMPORTANT:")
        print("• SQLite database was NOT modified.")
        print("• Original ZIP was NOT modified.")
        print("• PDFs were processed only in memory.")


if __name__ == "__main__":
    main()