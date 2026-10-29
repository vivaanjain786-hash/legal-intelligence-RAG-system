import re

from parser.base_parser import BaseParser


class OldMinimalParser(BaseParser):

    # ============================================================
    # FORMAT DETECTION
    # ============================================================
    
    def can_parse(self, text: str) -> bool:
       """
    Detect Indian Kanoon-style old minimal judgments.

    Typical structure:

        Title + date
        Equivalent citations:
        Author:
        Bench:
        JUDGMENT / ORDER

    PDF extraction is inconsistent. In particular,
    "Equivalent citations" may appear as:

        Equivalent citations:

    or:

        E q u i v a l e n t  c i t a t i o n s :

    Therefore the header is normalized before detection.
    """

       first = text[:12000]

    # ----------------------------------------------------
    # Normalize PDF spacing artifacts
    # ----------------------------------------------------
       normalized = re.sub(
        r"\s+",
        " ",
        first
       ).strip()

    # Remove spaces between individual letters when the
    # extracted PDF has produced:
    #
    # E q u i v a l e n t c i t a t i o n s
    #
    # This is deliberately limited to the known header.
       normalized_header = re.sub(
        r"E\s*q\s*u\s*i\s*v\s*a\s*l\s*e\s*n\s*t\s+"
        r"c\s*i\s*t\s*a\s*t\s*i\s*o\s*n\s*s",
        "Equivalent citations",
        normalized,
        flags=re.IGNORECASE
       )

    # ----------------------------------------------------
    # Equivalent citations
    # ----------------------------------------------------
       has_citation = re.search(
        r"Equivalent\s+citations\s*:",
        normalized_header,
        re.IGNORECASE
       ) is not None

    # ----------------------------------------------------
    # JUDGMENT / ORDER
    # ----------------------------------------------------
       has_judgment_or_order = re.search(
        r"\b(?:JUDGMENT|ORDER)\b",
        first,
        re.IGNORECASE
       ) is not None

    # ----------------------------------------------------
    # Old Indian Kanoon title + date
    #
    # Example:
    #
    # Ramaswamy Kalingaryar vs Mathayan Padayachi
    # on 30 August, 1991
    #
    # Newlines are already normalized above.
    # ----------------------------------------------------
       has_old_style_title = re.search(
        r"\bon\s+"
        r"\d{1,2}\s+"
        r"[A-Za-z]+\s*,?\s*"
        r"\d{4}\b",
        normalized,
        re.IGNORECASE
       ) is not None

    # ----------------------------------------------------
    # Structured fields
    #
    # If these exist, OldStructuredParser should handle
    # the document instead.
    # ----------------------------------------------------
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

       return (
        has_citation
        and has_judgment_or_order
        and has_old_style_title
        and not has_structured_fields
    )
    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def clean(value):
        if not value:
            return None

        value = re.sub(r"\s+", " ", value)
        value = value.strip(" .,:;-")

        return value or None

    @staticmethod
    def unique(values):
        result = []

        for value in values:
            value = OldMinimalParser.clean(value)

            if value and value not in result:
                result.append(value)

        return result

    # ============================================================
    # PARSER
    # ============================================================

    def parse(self, text: str) -> dict:

        # Header only.
        # We deliberately avoid searching the entire judgment.
        first = text[:12000]

        data = {
            "format": "old_minimal",
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
        #
        # The title is the text before the FIRST "on <date>"
        # occurrence at the beginning of the document.
        #
        # This handles titles that wrap across multiple PDF lines.
        # ========================================================

        header_match = re.search(
            r"(?is)^\s*(.*?)\s+on\s+"
            r"\d{1,2}\s+[A-Za-z]+,?\s+\d{4}",
            first[:3000]
        )

        if header_match:
            data["title"] = self.clean(
                header_match.group(1)
            )

        # ========================================================
        # DECISION DATE
        # ========================================================

        date_match = re.search(
            r"\bon\s+"
            r"(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})",
            first[:3000],
            re.IGNORECASE
        )

        if date_match:
            data["decision_date"] = self.clean(
                date_match.group(1)
            )

        # ========================================================
        # COURT
        # ========================================================

        if re.search(
            r"SUPREME\s+COURT\s+OF\s+INDIA",
            first,
            re.IGNORECASE
        ):
            data["court"] = "Supreme Court of India"

        elif re.search(
            r"SUPREME\s+COURT",
            first,
            re.IGNORECASE
        ):
            data["court"] = "Supreme Court"

        # ========================================================
        # EQUIVALENT CITATIONS
        # ========================================================

        citation_match = re.search(
            r"Equivalent citations\s*:\s*"
            r"(.*?)"
            r"(?=\n\s*(?:Author:|Bench:|"
            r"JUDGMENT\b|ORDER\b|$))",
            first,
            re.IGNORECASE | re.DOTALL
        )

        if citation_match:
            citation = self.clean(
                citation_match.group(1)
            )

            if citation:
                data["citation"] = citation

        # ========================================================
        # AUTHOR
        # ========================================================

        author_match = re.search(
            r"(?im)^\s*Author\s*:\s*(.+?)\s*$",
            first
        )

        if author_match:
            data["author"] = self.clean(
                author_match.group(1)
            )

        # ========================================================
        # BENCH
        # ========================================================

        bench_match = re.search(
            r"(?im)^\s*Bench\s*:\s*(.+?)\s*$",
            first
        )

        if bench_match:
            data["bench"] = self.clean(
                bench_match.group(1)
            )

        # ========================================================
        # JUDGE
        #
        # Examples:
        #
        # JUDGMENT
        # A.P. Misra, J.
        #
        # ORDER
        # A.P. Misra, J.
        # ========================================================

        judge_match = re.search(
            r"(?is)"
            r"^\s*(?:JUDGMENT|ORDER)\s*:?\s*$"
            r"\s*"
            r"([A-Za-z][A-Za-z .,'()&-]*?,?\s*J\.?)"
            r"\s*(?:\n|$)",
            first,
            re.MULTILINE
        )

        if judge_match:
            judge = self.clean(
                judge_match.group(1)
            )

            if judge:
                data["judge"] = judge

        # ========================================================
        # CASE TYPE
        #
        # Keep this conservative. We only accept known legal
        # proceeding names.
        # ========================================================

        case_patterns = [
            r"\b(Civil Appeal)\b",
            r"\b(Criminal Appeal)\b",
            r"\b(Civil Revision)\b",
            r"\b(Criminal Revision)\b",
            r"\b(Special Leave Petition)\b",
            r"\b(Writ Petition)\b",
            r"\b(Transfer Petition)\b",
            r"\b(Contempt Petition)\b",
        ]

        for pattern in case_patterns:

            match = re.search(
                pattern,
                first,
                re.IGNORECASE
            )

            if match:
                data["case_type"] = self.clean(
                    match.group(1)
                ).title()
                break

        # ========================================================
        # CASE NUMBER
        #
        # IMPORTANT:
        # Do NOT use a generic "No." or "of YYYY" pattern.
        #
        # Otherwise phrases such as:
        # "Act of 1951"
        #
        # can be incorrectly interpreted as a case number.
        # ========================================================

        case_number_patterns = [
            r"\b(?:Civil|Criminal)\s+"
            r"(?:Appeal|Revision)"
            r"\s+(?:No\.?|Nos\.?)\s*"
            r"([A-Za-z0-9./-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9./-]+)?"
            r"\s+of\s+\d{4})",

            r"\bSpecial Leave Petition\s+"
            r"(?:No\.?|Nos\.?)\s*"
            r"([A-Za-z0-9./-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9./-]+)?"
            r"\s+of\s+\d{4})",

            r"\bWrit Petition\s+"
            r"(?:No\.?|Nos\.?)\s*"
            r"([A-Za-z0-9./-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9./-]+)?"
            r"\s+of\s+\d{4})",

            r"\bTransfer Petition\s+"
            r"(?:No\.?|Nos\.?)\s*"
            r"([A-Za-z0-9./-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9./-]+)?"
            r"\s+of\s+\d{4})",

            r"\bContempt Petition\s+"
            r"(?:No\.?|Nos\.?)\s*"
            r"([A-Za-z0-9./-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9./-]+)?"
            r"\s+of\s+\d{4})",
        ]

        for pattern in case_number_patterns:

            match = re.search(
                pattern,
                first,
                re.IGNORECASE
            )

            if match:
                value = self.clean(
                    match.group(1)
                )

                if value:
                    data["case_number"] = value

                break

        # ========================================================
        # ACTS
        # ========================================================

        act_match = re.search(
            r"(?is)"
            r"^\s*ACT\s*:\s*(.*?)"
            r"(?=\n\s*HEADNOTE\s*:|"
            r"\n\s*JUDGMENT\b|"
            r"\n\s*ORDER\b|"
            r"$)",
            first
        )

        if act_match:

            act_section = act_match.group(1)

            act_matches = re.findall(
                r"\b("
                r"(?:[A-Z][A-Za-z&.'()/-]*\s+){1,8}"
                r"Act"
                r"(?:,\s*\d{4})?"
                r")\b",
                act_section
            )

            acts = self.unique(
                act_matches
            )

            if acts:
                data["acts"] = ", ".join(acts)

        # ========================================================
        # ARTICLES
        # ========================================================

        article_matches = re.findall(
            r"\bArticle\s+\d+"
            r"(?:\s*\(\s*\d+[A-Za-z]*\s*\))*",
            first,
            re.IGNORECASE
        )

        articles = []

        for article in article_matches:

            article = re.sub(
                r"\s+",
                " ",
                article
            ).strip()

            article = re.sub(
                r"\s*\(\s*",
                "(",
                article
            )

            article = re.sub(
                r"\s*\)",
                ")",
                article
            )

            article = self.clean(
                article
            )

            if (
                article
                and article not in articles
            ):
                articles.append(article)

        if articles:
            data["articles"] = ", ".join(
                articles
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