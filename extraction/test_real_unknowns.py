import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from parser.parser_factory import ParserFactory
from parser.parsers.modern_parser import ModernParser
from parser.parsers.old_structured_parser import OldStructuredParser
from parser.parsers.old_minimal_parser import OldMinimalParser


DB_PATH = PROJECT_ROOT / "data" / "legal_dataset.db"


TEST_FILES = [
    "2011/Academy_Of_Nutrition_Improvement_Ors_vs_Union_Of_India_on_4_July_2011_1.PDF",
    "2013/Laxmibai_Dead_Thru_Lr_S_Anr_vs_Bhagwanthbuva_Dead_Thru_Lr_S_Ors_on_29_January_2013.PDF",
    "2021/Bharat_Chaudhary_vs_Union_Of_India_on_13_December_2021_1.PDF",
    "2010/Gen_Manager_Punjab_Sind_Bank_Ors_vs_Daya_Singh_on_28_July_2010_1.PDF",
    "2013/M_S_Mutha_Associates_Ors_vs_State_Of_Maharashtra_Ors_on_4_July_2013_1.PDF",
]


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

factory = ParserFactory()

print("=" * 80)
print("REAL UNKNOWN CASE PARSER TEST")
print("=" * 80)


for filename in TEST_FILES:

    print()
    print("-" * 80)
    print("FILE:", filename)

    cursor.execute("""
        SELECT id, clean_text
        FROM cases
        WHERE filename = ?
    """, (filename,))

    row = cursor.fetchone()

    if not row:
        print("❌ NOT FOUND IN DATABASE")
        continue

    case_id, text = row

    print("CASE ID:", case_id)
    print("TEXT LENGTH:", len(text))

    modern = ModernParser()
    structured = OldStructuredParser()
    minimal = OldMinimalParser()

    print()
    print("ModernParser       :", modern.can_parse(text))
    print("OldStructuredParser:", structured.can_parse(text))
    print("OldMinimalParser   :", minimal.can_parse(text))

    result = factory.get_parser(text)

    print()
    print(
        "FACTORY RESULT     :",
        result.__class__.__name__
        if result
        else "UNKNOWN"
    )

    print()
    print("FIRST 20 LINES")
    print("-" * 40)

    for i, line in enumerate(text.splitlines()[:20], start=1):
        if line.strip():
            print(f"{i:02}: {line}")


conn.close()

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)