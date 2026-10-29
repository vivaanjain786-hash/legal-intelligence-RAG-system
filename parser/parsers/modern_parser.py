import re

from parser.base_parser import BaseParser


class ModernParser(BaseParser):

       # ============================================================
    # FORMAT DETECTION
    # ============================================================

    def can_parse(self, text: str) -> bool:
        """
        Detect modern and semi-modern Supreme Court judgment/order documents.

        Handles:
        - Standard "SUPREME COURT OF INDIA"
        - PDF-extracted "SUPREMECOURT OF INDIA"
        - Modern INSC cases
        - Reportable judgments
        - Civil / Criminal / Original jurisdictions
        - Modern case-number variants
        - "PETITION FOR SPECIAL LEAVE TO APPEAL"
        - Spaced decision markers such as "J U D G M E N T"
        - Older Supreme Court documents containing
          "The Judgment of the Court was delivered by"
        """

        first = text[:12000]

        # --------------------------------------------------------
        # Supreme Court identification
        # --------------------------------------------------------

        has_supreme_court = re.search(
            r"\b(?:THE\s+)?SUPREME\s*COURT\s+OF\s+INDIA\b",
            first,
            re.IGNORECASE
        ) is not None

        # --------------------------------------------------------
        # Modern Supreme Court citation
        # --------------------------------------------------------

        has_insc = re.search(
            r"\b\d{4}\s*INSC\s*\d+\b",
            first,
            re.IGNORECASE
        ) is not None

        # --------------------------------------------------------
        # Reportable marker
        # --------------------------------------------------------

        has_reportable = re.search(
            r"\bREPORTABLE\b",
            first,
            re.IGNORECASE
        ) is not None

        # --------------------------------------------------------
        # Supreme Court jurisdiction
        # --------------------------------------------------------

        has_jurisdiction = re.search(
            r"\b(?:"
            r"CIVIL\s+(?:APPELLATE|ORIGINAL)\s+JURISDICTION|"
            r"CRIMINAL\s+(?:APPELLATE|ORIGINAL)\s+JURISDICTION|"
            r"ORIGINAL\s+JURISDICTION"
            r")\b",
            first,
            re.IGNORECASE
        ) is not None

        # --------------------------------------------------------
        # Case-number structures
        # --------------------------------------------------------

        has_case_number = re.search(
            r"(?im)^\s*(?:"
            r"SLP\s*\([^)]*\)\s+NO(?:\(S\)|S)?\.?|"
            r"CRIMINAL\s+APPEAL\s+NO(?:\(S\)|S)?\.?|"
            r"CIVIL\s+APPEAL\s+NO(?:\(S\)|S)?\.?|"
            r"WRIT\s+PETITION(?:\s*[\(\[][^\)\]]*[\)\]])?\s+NO(?:\(S\)|S)?\.?|"
            r"SPECIAL\s+LEAVE\s+PETITION(?:\s*\([^)]*\))?\s+NO(?:\(S\)|S)?\.?|"
            r"PETITION\s+FOR\s+SPECIAL\s+LEAVE\s+TO\s+APPEAL(?:\s*\([^)]*\))?\s+NO(?:\(S\)|S)?\.?|"
            r"TRANSFER\s+PETITION(?:\s*\([^)]*\))?\s+NO(?:\(S\)|S)?\.?|"
            r"CONTEMPT\s+PETITION(?:\s*\([^)]*\))?\s+NO(?:\(S\)|S)?\.?"
            r")",
            first,
            re.IGNORECASE
        ) is not None

        # --------------------------------------------------------
        # Judgment / order marker
        # --------------------------------------------------------

        has_decision_marker = re.search(
            r"(?im)^\s*"
            r"(?:"
            r"J\s*U\s*D\s*G\s*M\s*E\s*N\s*T|"
            r"J\s*U\s*D\s*G\s*E\s*M\s*E\s*N\s*T|"
            r"O\s*R\s*D\s*E\s*R"
            r")"
            r"\s*:?\s*$",
            first
        ) is not None

        # --------------------------------------------------------
        # Author / Bench metadata
        # --------------------------------------------------------

        has_author = re.search(
            r"(?im)^\s*Author\s*:",
            first
        ) is not None

        has_bench = re.search(
            r"(?im)^\s*Bench\s*:",
            first
        ) is not None

        # --------------------------------------------------------
        # Older Supreme Court judgment format
        # --------------------------------------------------------

        has_old_judgment_delivery = re.search(
            r"The\s+Judgment\s+of\s+the\s+Court\s+was\s+delivered\s+by",
            first,
            re.IGNORECASE
        ) is not None

        has_old_case_number = re.search(
            r"\(\s*(?:"
            r"Civil\s+Appeal|"
            r"Criminal\s+Appeal|"
            r"Writ\s+Petition|"
            r"Special\s+Leave\s+Petition"
            r")\s+No\.?",
            first,
            re.IGNORECASE
        ) is not None

        # --------------------------------------------------------
        # Classification logic
        # --------------------------------------------------------

        if has_insc:
            return True

        if has_reportable and has_supreme_court:
            return True

        if (
            has_supreme_court
            and has_jurisdiction
            and has_case_number
            and has_decision_marker
        ):
            return True

        if (
            has_supreme_court
            and has_author
            and has_bench
            and has_case_number
            and has_decision_marker
        ):
            return True

        if (
            has_old_judgment_delivery
            and has_old_case_number
            and has_bench
        ):
            return True

        return False

    # ============================================================
    # COMMON CLEANING
    # ============================================================

    @staticmethod
    def clean(value):
        if not value:
            return None

        value = value.replace("\r", " ")
        value = re.sub(r"\s+", " ", value)
        value = value.strip(" .,:;-")

        return value or None

    # ============================================================
    # HEADER
    # ============================================================

    @staticmethod
    def get_header(text: str) -> str:
        """
        Extract the portion containing the Supreme Court header.

        We deliberately stop before the actual judgment/order body.
        """

        first = text[:12000]

        court_match = re.search(
            r"IN THE SUPREME COURT OF INDIA",
            first,
            re.IGNORECASE
        )

        if court_match:
            header = first[court_match.start():]
        else:
            header = first

        # Stop before the actual judgment/order body.
        judgment_match = re.search(
            r"(?im)^\s*(?:JUDGMENT|ORDER)\s*:?\s*$",
            header
        )

        if judgment_match:
            header = header[:judgment_match.start()]

        return header

    # ============================================================
    # TITLE
    # ============================================================

    def extract_title(self, text: str):
        match = re.search(
            r"(?is)^\s*(.*?)\s+vs\.?\s+"
            r"(.*?)\s+on\s+"
            r"\d{1,2}\s+[A-Za-z]+,?\s+\d{4}",
            text[:3000]
        )

        if match:
            petitioner = self.clean(match.group(1))
            respondent = self.clean(match.group(2))

            if petitioner and respondent:
                return f"{petitioner} vs {respondent}"

        return None

    # ============================================================
    # DATE
    # ============================================================

    def extract_date(self, text: str):
        match = re.search(
            r"\bon\s+"
            r"(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})",
            text[:3000],
            re.IGNORECASE
        )

        if match:
            return self.clean(match.group(1))

        return None

    # ============================================================
    # COURT
    # ============================================================

    def extract_court(self, text: str):
        if re.search(
            r"IN THE SUPREME COURT OF INDIA",
            text,
            re.IGNORECASE
        ):
            return "SUPREME COURT OF INDIA"

        return None

    # ============================================================
    # CITATION
    # ============================================================

    def extract_citation(self, text: str):
        match = re.search(
            r"\b(\d{4}\s+INSC\s+\d+)\b",
            text[:8000],
            re.IGNORECASE
        )

        if match:
            return self.clean(match.group(1))

        return None

    # ============================================================
    # CASE TYPE
    # ============================================================

    def extract_case_type(self, text: str):
        patterns = [
            r"(?im)^\s*(CRIMINAL\s+ORIGINAL\s+JURISDICTION)\s*$",
            r"(?im)^\s*(CRIMINAL\s+APPELLATE\s+JURISDICTION)\s*$",
            r"(?im)^\s*(CIVIL\s+APPELLATE\s+JURISDICTION)\s*$",
            r"(?im)^\s*(CIVIL\s+ORIGINAL\s+JURISDICTION)\s*$",
            r"(?im)^\s*(ORIGINAL\s+JURISDICTION)\s*$",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text[:8000]
            )

            if match:
                return self.clean(match.group(1)).title()

        return None

    # ============================================================
    # CASE NUMBER
    # ============================================================

    def extract_case_number(self, header: str):
        """
        Extract the PRIMARY case number from the Supreme Court header.

        Only the header is searched so references appearing later in
        the judgment cannot be mistaken for the primary case number.
        """

        patterns = [

            # ----------------------------------------------------
            # SLP(CIVIL) NO(S). 999-1001 OF 2025
            # ----------------------------------------------------
            r"(?im)^\s*"
            r"(SLP\s*\([^)]*\)\s+NO(?:\(S\)|S)?\.?\s*"
            r"[A-Za-z0-9()/-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9()/-]+)?"
            r"\s+OF\s+\d{4})\s*$",

            # ----------------------------------------------------
            # CRIMINAL APPEAL NO. 722 OF 2012
            # ----------------------------------------------------
            r"(?im)^\s*"
            r"(CRIMINAL\s+APPEAL\s+NO(?:\(S\)|S)?\.?\s*"
            r"[A-Za-z0-9()/-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9()/-]+)?"
            r"\s+OF\s+\d{4})\s*$",

            # ----------------------------------------------------
            # CIVIL APPEAL NOS.11070 - 11071 OF 2024
            # ----------------------------------------------------
            r"(?im)^\s*"
            r"(CIVIL\s+APPEAL\s+NO(?:\(S\)|S)?\.?\s*"
            r"[A-Za-z0-9()/-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9()/-]+)?"
            r"\s+OF\s+\d{4})\s*$",

            # ----------------------------------------------------
            # WRIT PETITION (CRIMINAL) NO. 340 OF 2024
            # ----------------------------------------------------
            r"(?im)^\s*"
            r"(WRIT\s+PETITION"
            r"(?:\s*\([^)]*\))?"
            r"\s+NO(?:\(S\)|S)?\.?\s*"
            r"[A-Za-z0-9()/-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9()/-]+)?"
            r"\s+OF\s+\d{4})\s*$",

            # ----------------------------------------------------
            # SPECIAL LEAVE PETITION
            # ----------------------------------------------------
            r"(?im)^\s*"
            r"(SPECIAL\s+LEAVE\s+PETITION"
            r"(?:\s*\([^)]*\))?"
            r"\s+NO(?:\(S\)|S)?\.?\s*"
            r"[A-Za-z0-9()/-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9()/-]+)?"
            r"\s+OF\s+\d{4})\s*$",

            # ----------------------------------------------------
            # TRANSFER PETITION
            # ----------------------------------------------------
            r"(?im)^\s*"
            r"(TRANSFER\s+PETITION"
            r"(?:\s*\([^)]*\))?"
            r"\s+NO(?:\(S\)|S)?\.?\s*"
            r"[A-Za-z0-9()/-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9()/-]+)?"
            r"\s+OF\s+\d{4})\s*$",

            # ----------------------------------------------------
            # CONTEMPT PETITION
            # ----------------------------------------------------
            r"(?im)^\s*"
            r"(CONTEMPT\s+PETITION"
            r"(?:\s*\([^)]*\))?"
            r"\s+NO(?:\(S\)|S)?\.?\s*"
            r"[A-Za-z0-9()/-]+"
            r"(?:\s*[-–]\s*[A-Za-z0-9()/-]+)?"
            r"\s+OF\s+\d{4})\s*$",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                header
            )

            if match:
                return self.clean(match.group(1))

        return None

    # ============================================================
    # PARTIES
    # ============================================================

    def extract_parties(self, header: str):

        petitioner = None
        respondent = None

        # Find VERSUS first.
        versus_match = re.search(
            r"(?im)^\s*VERSUS\s*$",
            header
        )

        if not versus_match:
            versus_match = re.search(
                r"\bVERSUS\b",
                header,
                re.IGNORECASE
            )

        if not versus_match:
            return None, None

        before_versus = header[:versus_match.start()]
        after_versus = header[versus_match.end():]

        # Find the primary case number.
        case_number = self.extract_case_number(header)

        if case_number:
            case_position = header.find(case_number)

            if case_position >= 0:
                before_versus = header[
                    case_position + len(case_number):
                    versus_match.start()
                ]

        # --------------------------------------------------------
        # PETITIONER
        # --------------------------------------------------------

        petitioner_lines = []

        for line in before_versus.splitlines():

            line = line.strip()

            if not line:
                continue

            # Ignore metadata/header lines.
            if re.match(
                r"^(AUTHOR|BENCH|REPORTABLE|IN THE SUPREME COURT|"
                r"\d{4}\s+INSC|CIVIL|CRIMINAL|ORIGINAL|APPELLATE|"
                r"JURISDICTION)\b",
                line,
                re.IGNORECASE
            ):
                continue

            # Ignore case-number fragments.
            if re.search(
                r"\bNO(?:S)?\.?\b.*\bOF\s+\d{4}\b",
                line,
                re.IGNORECASE
            ):
                continue

            petitioner_lines.append(line)

        if petitioner_lines:
            petitioner = petitioner_lines[-1]

        # --------------------------------------------------------
        # RESPONDENT
        # --------------------------------------------------------

        respondent_lines = []

        for line in after_versus.splitlines():

            line = line.strip()

            if not line:
                continue

            # Stop at the next section.
            if re.match(
                r"^(JUDGMENT|ORDER|WITH|DATE OF JUDGMENT|BENCH)\b",
                line,
                re.IGNORECASE
            ):
                break

            respondent_lines.append(line)

        if respondent_lines:
            respondent = respondent_lines[0]

        petitioner = self.clean_party(petitioner)
        respondent = self.clean_party(respondent)

        return petitioner, respondent

    # ============================================================
    # PARTY CLEANING
    # ============================================================

    def clean_party(self, value):

        if not value:
            return None

        value = value.replace("\r", " ")
        value = value.replace("\n", " ")

        # Remove PDF dotted formatting.
        value = re.sub(
            r"\.{2,}",
            " ",
            value
        )

        # Remove appellant/petitioner labels.
        value = re.sub(
            r"\b(?:APPELLANT|APPELLANTS|PETITIONER|PETITIONERS)\b"
            r"(?:\s*\([^)]*\))?",
            "",
            value,
            flags=re.IGNORECASE
        )

        # Remove respondent labels.
        value = re.sub(
            r"\b(?:RESPONDENT|RESPONDENTS)\b"
            r"(?:\s*\([^)]*\))?",
            "",
            value,
            flags=re.IGNORECASE
        )

        # Remove trailing PDF extraction "RE".
        value = re.sub(
            r"\s+\bRE\b\s*$",
            "",
            value,
            flags=re.IGNORECASE
        )

        # Remove known PDF column artefact.
        # Example:
        # A RAJENDRA AP
        # becomes:
        # A RAJENDRA
        value = re.sub(
            r"\s+\bAP\b\s*$",
            "",
            value,
            flags=re.IGNORECASE
        )

        value = self.clean(value)

        return value

    # ============================================================
    # AUTHOR
    # ============================================================

    def extract_author(self, text: str):

        match = re.search(
            r"(?im)^\s*Author\s*:\s*(.+?)\s*$",
            text[:5000]
        )

        if match:
            return self.clean(match.group(1))

        return None

    # ============================================================
    # BENCH
    # ============================================================

    def extract_bench(self, text: str):

        match = re.search(
            r"(?im)^\s*Bench\s*:\s*(.+?)\s*$",
            text[:5000]
        )

        if match:
            return self.clean(match.group(1))

        return None

    # ============================================================
    # JUDGE
    # ============================================================

        # ============================================================
    # JUDGE
    # ============================================================

    def extract_judge(self, text: str):
        """
        Extract the judge(s) responsible for the judgment/order.

        Handles:
        1. Judge immediately after JUDGMENT / ORDER
        2. Signature block near the end of short orders

        We avoid searching the entire body indiscriminately because
        judgments frequently refer to other judges and courts.
        """

        first = text[:12000]
        lines = first.splitlines()

        decision_index = None

        # --------------------------------------------------------
        # Find JUDGMENT / ORDER heading
        # --------------------------------------------------------

        for i, line in enumerate(lines):

            normalized = re.sub(
                r"\s+",
                "",
                line.upper()
            )

            if normalized.startswith("JUDGMENT"):
                decision_index = i
                break

            if normalized == "ORDER" or normalized.startswith("ORDER:"):
                decision_index = i
                break

        # --------------------------------------------------------
        # 1. Judge immediately after JUDGMENT / ORDER
        # --------------------------------------------------------

        if decision_index is not None:

            for line in lines[
                decision_index + 1:
                decision_index + 5
            ]:

                line = line.strip()

                if not line:
                    continue

                # Examples:
                # Mehta, J.
                # UJJAL BHUYAN, J.
                # D. P. MOHAPATRA, J.
                match = re.match(
                    r"^([A-Za-z][A-Za-z .,'()&-]*,\s*J{1,2}\.?)$",
                    line
                )

                if match:
                    return self.clean(match.group(1))

                # Stop if actual judgment/order text begins.
                if re.match(
                    r"^(Having|This|The|Heard|We|1\.)\b",
                    line,
                    re.IGNORECASE
                ):
                    break

        # --------------------------------------------------------
        # 2. Look for signature block near the end
        #
        # Example:
        #
        # ................CJI.
        # (SANJIV KHANNA) ..................J. (SANJAY KUMAR)
        # --------------------------------------------------------

        tail = text[-3000:]

        # Typical Supreme Court signature format.
        signature_match = re.search(
            r"\(([^()\n]+)\)"
            r"\s*[-. ]*"
            r"(?:CJI|J\.?)"
            r".*?"
            r"\(([^()\n]+)\)",
            tail,
            re.IGNORECASE
        )

        if signature_match:

            first_judge = self.clean(
                signature_match.group(1)
            )

            second_judge = self.clean(
                signature_match.group(2)
            )

            judges = []

            if first_judge:
                judges.append(first_judge)

            if second_judge:
                judges.append(second_judge)

            if judges:
                return ", ".join(judges)

        # --------------------------------------------------------
        # Alternative single-judge signature near the end
        # --------------------------------------------------------

        single_signature_matches = re.findall(
            r"\(([A-Z][A-Z .,'-]{2,})\)"
            r"\s*[-. ]*"
            r"(?:CJI|J)\.?",
            tail
        )

        if single_signature_matches:

            judges = []

            for judge in single_signature_matches:

                judge = self.clean(judge)

                if judge and judge not in judges:
                    judges.append(judge)

            if judges:
                return ", ".join(judges)

        return None

    # ============================================================
    # REPORTABLE
    # ============================================================

    def extract_reportable(self, text: str):

        if re.search(
            r"\bREPORTABLE\b",
            text[:8000],
            re.IGNORECASE
        ):
            return "Yes"

        return "No"

    # ============================================================
    # ACTS
    # ============================================================

    def extract_acts(self, text: str):
        """
        Disabled temporarily.

        A dedicated legal-entity extractor will be implemented
        later because Acts occur throughout the judgment body.
        """

        return None

    # ============================================================
    # ARTICLES
    # ============================================================

    def extract_articles(self, text: str):

        matches = re.findall(
            r"\bArticle\s+\d+"
            r"(?:\s*\(\s*\d+[A-Za-z]*\s*\))*",
            text[:12000],
            re.IGNORECASE
        )

        articles = []

        for article in matches:

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

            article = self.clean(article)

            if article and article not in articles:
                articles.append(article)

        if articles:
            return ", ".join(articles)

        return None

    # ============================================================
    # MAIN PARSER
    # ============================================================

    def parse(self, text: str):

        header = self.get_header(text)

        petitioner, respondent = self.extract_parties(header)

        return {
            "format": "modern",

            "title": self.extract_title(text),

            "decision_date": self.extract_date(text),

            "court": self.extract_court(text),

            "citation": self.extract_citation(text),

            "case_type": self.extract_case_type(text),

            "case_number": self.extract_case_number(header),

            "author": self.extract_author(text),

            "bench": self.extract_bench(text),

            "judge": self.extract_judge(text),

            "petitioner": petitioner,

            "respondent": respondent,

            "reportable": self.extract_reportable(text),

            "acts": self.extract_acts(text),

            "articles": self.extract_articles(text),
        }