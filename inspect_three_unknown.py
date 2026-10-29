import zipfile
import re
from pathlib import Path
import pymupdf as fitz

ZIP_PATH = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset.zip")

TEST_FILES = [
    "Ramaswamy_Kalingaryar_vs_Mathayan_Padayachi_on_30_August_1991_1.PDF",
    "Commissioner_Of_Income_Tax_Shillong_vs_Assam_Travels_Shipping_Service_on_24_September_1992_1.PDF",
    "Rama_Meru_And_Another_vs_State_Of_Gujarat_on_12_March_1992_1.PDF",
]

for filename in TEST_FILES:

    print()
    print("=" * 80)
    print(filename)
    print("=" * 80)

    with zipfile.ZipFile(ZIP_PATH, "r") as z:

        matches = [
            name for name in z.namelist()
            if Path(name).name == filename
        ]

        with z.open(matches[0]) as f:
            pdf = fitz.open(
                stream=f.read(),
                filetype="pdf"
            )

            text = "\n".join(
                page.get_text("text")
                for page in pdf
            )

            pdf.close()

    first = text[:12000]

    # Same normalization used by parser
    normalized = re.sub(
        r"\s+",
        " ",
        first
    ).strip()

    normalized_header = re.sub(
        r"E\s*q\s*u\s*i\s*v\s*a\s*l\s*e\s*n\s*t\s+"
        r"c\s*i\s*t\s*a\s*t\s*i\s*o\s*n\s*s",
        "Equivalent citations",
        normalized,
        flags=re.IGNORECASE
    )

    has_citation = re.search(
        r"Equivalent\s+citations\s*:",
        normalized_header,
        re.IGNORECASE
    ) is not None

    has_judgment_or_order = re.search(
        r"\b(?:JUDGMENT|ORDER)\b",
        first,
        re.IGNORECASE
    ) is not None

    has_old_style_title = re.search(
        r"\bon\s+"
        r"\d{1,2}\s+"
        r"[A-Za-z]+\s*,?\s*"
        r"\d{4}\b",
        normalized,
        re.IGNORECASE
    ) is not None

    has_structured_fields = (
        re.search(
            r"(?im)^\s*PETITIONER\s*:",
            first
        ) is not None
        or
        re.search(
            r"(?im)^\s*RESPONDENT\s*:",
            first
        ) is not None
        or
        re.search(
            r"(?im)^\s*DATE\s+OF\s+JUDGMENT\s*:?",
            first
        ) is not None
    )

    print()
    print("has_citation          :", has_citation)
    print("has_judgment_or_order :", has_judgment_or_order)
    print("has_old_style_title   :", has_old_style_title)
    print("has_structured_fields :", has_structured_fields)

    print()
    print("FINAL RESULT          :",
          has_citation
          and has_judgment_or_order
          and has_old_style_title
          and not has_structured_fields)

    print()
    print("NORMALIZED HEADER:")
    print(normalized[:1000])