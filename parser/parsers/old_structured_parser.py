import re

from parser.base_parser import BaseParser


class OldStructuredParser(BaseParser):

    def can_parse(self, text: str) -> bool:
        """
        Detect old structured Supreme Court judgments.

        The structured header is usually composed of:

            PETITIONER:
            RESPONDENT:
            DATE OF JUDGMENT...

        Older PDFs are inconsistent about whether a colon or space
        appears after "DATE OF JUDGMENT", so detection must not
        depend on an exact literal string.
        """

        first = text[:8000]

        has_petitioner = re.search(
            r"(?im)^\s*PETITIONER\s*:",
            first
        ) is not None

        has_respondent = re.search(
            r"(?im)^\s*RESPONDENT\s*:",
            first
        ) is not None

        has_date = re.search(
            r"(?im)^\s*DATE\s+OF\s+JUDGMENT\s*:?\s*"
            r"\d{1,2}\s*[/.-]\s*\d{1,2}\s*[/.-]\s*\d{4}",
            first
        ) is not None

        return (
            has_petitioner
            and has_respondent
            and has_date
        )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def clean(value):

        if not value:
            return None

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        value = value.strip(
            " .,:;-"
        )

        return value or None

    @staticmethod
    def unique(values):

        result = []

        for value in values:

            value = OldStructuredParser.clean(
                value
            )

            if value and value not in result:
                result.append(value)

        return result

    # ============================================================
    # PARSER
    # ============================================================

    def parse(self, text: str) -> dict:

        first = text[:12000]

        data = {
            "format": "old_structured",
            "title": None,
            "decision_date": None,
            "court": None,
            "citation": None,
            "case_type": None,
            "case_number": None,
            "author": None,
            "bench": None,
            "judge": None,
            "petitioner": None,
            "respondent": None,
            "reportable": "Unknown",
            "acts": None,
            "articles": None,
        }

        # ========================================================
        # TITLE
        # ========================================================

        m = re.search(
            r"(?is)^\s*(.*?)\s+on\s+"
            r"\d{1,2}\s+[A-Za-z]+,?\s+\d{4}",
            first[:3000]
        )

        if m:
            data["title"] = self.clean(
                m.group(1)
            )

        # ========================================================
        # DATE
        # ========================================================

        date_patterns = [

            r"DATE\s+OF\s+JUDGMENT\s*:?\s*"
            r"(\d{1,2}\s*[/.-]\s*\d{1,2}\s*[/.-]\s*\d{4})",

            r"DATE\s+OF\s+JUDGMENT\s*:?\s*"
            r"(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})",

            r"\bon\s+"
            r"(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})",
        ]

        for pattern in date_patterns:

            m = re.search(
                pattern,
                first,
                re.IGNORECASE
            )

            if m:

                data["decision_date"] = self.clean(
                    m.group(1)
                )

                break

        # ========================================================
        # COURT
        # ========================================================

        if re.search(
            r"SUPREME\s+COURT\s+OF\s+INDIA",
            first,
            re.IGNORECASE
        ):

            data["court"] = (
                "Supreme Court of India"
            )

        elif re.search(
            r"SUPREME\s+COURT",
            first,
            re.IGNORECASE
        ):

            data["court"] = "Supreme Court"

        # ========================================================
        # CITATION
        # ========================================================

        m = re.search(
            r"Equivalent citations:\s*"
            r"(.*?)"
            r"(?=\n\s*(?:Author:|Bench:|"
            r"PETITIONER:|JUDGMENT\b|$))",
            first,
            re.IGNORECASE | re.DOTALL
        )

        if m:

            citation = self.clean(
                m.group(1)
            )

            if citation:
                data["citation"] = citation

        # ========================================================
        # AUTHOR
        # ========================================================

        m = re.search(
            r"(?m)^\s*Author:\s*(.+?)\s*$",
            first,
            re.IGNORECASE
        )

        if m:

            data["author"] = self.clean(
                m.group(1)
            )

        # ========================================================
        # BENCH
        # ========================================================

        m = re.search(
            r"(?is)"
            r"\bBench:\s*"
            r"(.*?)"
            r"(?=\n\s*(?:CASE\s+NO\.?:|"
            r"PETITIONER:|"
            r"RESPONDENT:|"
            r"DATE\s+OF\s+JUDGMENT|"
            r"CITATION:|"
            r"ACT:|"
            r"HEADNOTE:|"
            r"JUDGMENT\b|"
            r"$))",
            first
        )

        if m:

            bench = self.clean(
                m.group(1)
            )

            data["bench"] = (
                bench or None
            )

        # ========================================================
        # CASE NUMBER
        # ========================================================

        case_no_match = re.search(
            r"(?is)"
            r"^\s*CASE\s+NO\.?\s*:\s*"
            r"(.*?)"
            r"(?=\n\s*(?:PETITIONER:|"
            r"RESPONDENT:|"
            r"DATE\s+OF\s+JUDGMENT|"
            r"BENCH:|"
            r"CITATION:|"
            r"ACT:|"
            r"HEADNOTE:|"
            r"JUDGMENT\b|"
            r"$))",
            first,
            re.MULTILINE
        )

        if case_no_match:

            case_section = case_no_match.group(1)

            case_numbers = re.findall(
                r"\b(?:Civil|Criminal|"
                r"Special\s+Leave|"
                r"Writ|Transfer|Contempt)"
                r"\s+"
                r"(?:Appeal|Petition|Revision)"
                r"(?:\s*\([^)]+\))?"
                r"\s+"
                r"(?:No\.?\s*)?"
                r"[A-Za-z0-9./-]+"
                r"(?:\s*[-–]\s*[A-Za-z0-9./-]+)?"
                r"\s+of\s+\d{4}",
                case_section,
                re.IGNORECASE
            )

            case_numbers = self.unique(
                case_numbers
            )

            if case_numbers:

                data["case_number"] = (
                    "; ".join(case_numbers)
                )

            else:

                fallback_numbers = re.findall(
                    r"\b[A-Z]{1,8}"
                    r"(?:\s*[-–]\s*[A-Z0-9]+)?"
                    r"\s+of\s+\d{4}\b",
                    case_section
                )

                fallback_numbers = self.unique(
                    fallback_numbers
                )

                if fallback_numbers:

                    data["case_number"] = (
                        "; ".join(
                            fallback_numbers
                        )
                    )

        # ========================================================
        # PETITIONER
        # ========================================================

        m = re.search(
            r"(?is)"
            r"PETITIONER:\s*"
            r"(.*?)"
            r"(?=\n\s*(?:Vs\.?|V\.S\.?|"
            r"VERSUS|"
            r"RESPONDENT:))",
            first
        )

        if m:

            petitioner = self.clean(
                m.group(1)
            )

            data["petitioner"] = (
                petitioner or None
            )

        # ========================================================
        # RESPONDENT
        # ========================================================

        m = re.search(
            r"(?is)"
            r"RESPONDENT:\s*"
            r"(.*?)"
            r"(?=\n\s*(?:DATE\s+OF\s+JUDGMENT|"
            r"BENCH:|"
            r"CITATION:|"
            r"ACT:|"
            r"HEADNOTE:|"
            r"JUDGMENT\b|"
            r"$))",
            first
        )

        if m:

            respondent = self.clean(
                m.group(1)
            )

            data["respondent"] = (
                respondent or None
            )

        # ========================================================
        # JUDGE
        # ========================================================

        judge_match = re.search(
            r"The\s+Judgment\s+was\s+delivered\s+by\s+"
            r"([A-Za-z][A-Za-z .,'()&-]*,\s*J{1,2}\.?)",
            first,
            re.IGNORECASE
        )

        if judge_match:

            data["judge"] = self.clean(
                judge_match.group(1)
            )

        else:

            judgment_match = re.search(
                r"(?im)^\s*JUDGMENT\s*:?\s*$",
                first
            )

            if judgment_match:

                after_judgment = first[
                    judgment_match.end():
                ]

                judge_lines = (
                    after_judgment
                    .splitlines()[:5]
                )

                for line in judge_lines:

                    line = self.clean(line)

                    if not line:
                        continue

                    artifact_match = re.search(
                        r"J[\s.]+"
                        r"([A-Za-z][A-Za-z .,'()&-]*?)"
                        r"\s+J{1,2}\.?\s*$",
                        line
                    )

                    if artifact_match:

                        judge = self.clean(
                            artifact_match.group(1)
                        )

                        if judge:

                            data["judge"] = (
                                judge + ", J."
                            )

                            break

                    normal_match = re.match(
                        r"^([A-Za-z][A-Za-z .,'()&-]*?)"
                        r"\s+J{1,2}\.?\s*$",
                        line
                    )

                    if normal_match:

                        judge = self.clean(
                            normal_match.group(1)
                        )

                        if judge:

                            data["judge"] = (
                                judge + ", J."
                            )

                            break

        # ========================================================
        # CASE TYPE
        # ========================================================

        case_patterns = [

            r"\bCivil Appeal\b",
            r"\bCriminal Appeal\b",
            r"\bCivil Revision\b",
            r"\bCriminal Revision\b",
            r"\bSpecial Leave Petition\b",
            r"\bWrit Petition\b",
            r"\bTransfer Petition\b",
            r"\bContempt Petition\b",
        ]

        for pattern in case_patterns:

            m = re.search(
                pattern,
                first,
                re.IGNORECASE
            )

            if m:

                data["case_type"] = self.clean(
                    m.group(0)
                )

                break

        # ========================================================
        # ACTS
        # ========================================================

        m = re.search(
            r"(?is)"
            r"\bACT:\s*"
            r"(.*?)"
            r"(?=\n\s*HEADNOTE:|"
            r"\n\s*JUDGMENT\b|"
            r"\n\s*ORDER\b|"
            r"$)",
            first
        )

        if m:

            act_section = m.group(1)

            acts = re.findall(
                r"\b("
                r"[A-Z][A-Za-z&,.\- ]{2,100}"
                r"\bAct"
                r"(?:,\s*\d{4})?"
                r")\b",
                act_section
            )

            acts = self.unique(
                acts
            )

            if acts:

                data["acts"] = (
                    ", ".join(acts)
                )

        # ========================================================
        # ARTICLES
        # ========================================================

        articles = re.findall(
            r"\bArticle\s+\d+"
            r"(?:\s*\(\s*[0-9A-Za-z]+\s*\))*",
            first,
            re.IGNORECASE
        )

        articles = self.unique(
            articles
        )

        if articles:

            data["articles"] = (
                ", ".join(articles)
            )

        # ========================================================
        # REPORTABLE
        # ========================================================

        if re.search(
            r"\bREPORTABLE\b",
            first,
            re.IGNORECASE
        ):

            data["reportable"] = "Yes"

        return data