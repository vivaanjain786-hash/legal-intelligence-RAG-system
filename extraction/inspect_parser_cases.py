import zipfile
import re
from pathlib import Path

import pymupdf as fitz


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset")
ZIP_PATH = Path(r"C:\Users\Vivaan Jain\Downloads\Legal Dataset.zip")

# Exact files we want to inspect
TARGET_FILES = [
    "supreme_court_judgments/2000/A_Abdul_Rashid_Khan_Dead_And_Ors_vs_P_A_K_A_Shahul_Hamid_And_Ors_on_3_May_2000_1.PDF",

    "supreme_court_judgments/2000/A_P_Paper_Mills_Ltd_Etc_Etc_vs_Government_Of_A_P_And_Anr_on_28_September_2000_1.PDF",

    "supreme_court_judgments/2000/A_P_Pollution_Control_Board_Ii_vs_Prof_M_V_Nayudu_Retd_And_Ors_on_1_December_2000_1.PDF",

    "supreme_court_judgments/2025/A_Shankar_Savukku_Shankar_vs_State_Of_Tamil_Nadu_on_24_February_2025_1.PDF",

    "supreme_court_judgments/2025/Abdul_Nassar_vs_The_State_Of_Kerala_on_7_January_2025_1.PDF",

    "supreme_court_judgments/2025/Abdul_Wahid_vs_The_State_Of_Rajasthan_on_28_February_2025_1.PDF",
]

# Number of characters from the beginning of each PDF to display
HEADER_CHARS = 12000


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

    document.close()

    return text


# ============================================================
# MAIN
# ============================================================

print("=" * 80)
print("LEGAL INTELLIGENCE SYSTEM - RAW HEADER INSPECTION")
print("=" * 80)

print()
print(f"ZIP: {ZIP_PATH}")
print()

if not ZIP_PATH.exists():
    raise FileNotFoundError(
        f"ZIP file not found:\n{ZIP_PATH}"
    )


# ============================================================
# OPEN ZIP
# ============================================================

with zipfile.ZipFile(
    ZIP_PATH,
    "r"
) as zip_file:

    available_files = set(
        zip_file.namelist()
    )

    for index, pdf_name in enumerate(
        TARGET_FILES,
        start=1
    ):

        print()
        print("#" * 80)
        print(
            f"CASE {index}/{len(TARGET_FILES)}"
        )
        print("#" * 80)

        print()
        print(
            f"FILE:\n{pdf_name}"
        )

        print()

        # ----------------------------------------------------
        # Check file exists
        # ----------------------------------------------------

        if pdf_name not in available_files:

            print(
                "❌ FILE NOT FOUND IN ZIP"
            )

            continue


        # ----------------------------------------------------
        # Read PDF
        # ----------------------------------------------------

        try:

            with zip_file.open(
                pdf_name
            ) as pdf_file:

                pdf_bytes = pdf_file.read()


            text = extract_pdf_text(
                pdf_bytes
            )


            print(
                f"TOTAL CHARACTERS: {len(text):,}"
            )

            print()

            print(
                "=" * 80
            )

            print(
                f"FIRST {HEADER_CHARS:,} CHARACTERS"
            )

            print(
                "=" * 80
            )

            print()

            # ------------------------------------------------
            # IMPORTANT:
            # We deliberately DO NOT clean the text.
            #
            # We want to see the original line structure.
            # ------------------------------------------------

            print(
                text[:HEADER_CHARS]
            )

            print()

            print(
                "=" * 80
            )

            print(
                f"END OF HEADER FOR CASE {index}"
            )

            print(
                "=" * 80
            )


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
print("=" * 80)
print("RAW HEADER INSPECTION COMPLETE")
print("=" * 80)

print()
print("IMPORTANT:")
print("• SQLite database was NOT accessed.")
print("• SQLite database was NOT modified.")
print("• Original ZIP was NOT modified.")
print("• PDFs were read directly from the ZIP.")
print("• No parser was executed.")
print()