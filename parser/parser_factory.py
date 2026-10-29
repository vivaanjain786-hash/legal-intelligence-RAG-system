from parser.parsers.modern_parser import ModernParser
from parser.parsers.old_structured_parser import OldStructuredParser
from parser.parsers.old_minimal_parser import OldMinimalParser


class ParserFactory:

    def __init__(self):
        self.parsers = [
            ModernParser(),
            OldStructuredParser(),
            OldMinimalParser(),
        ]

    def get_parser(self, text: str):
        """
        Return the first parser capable of handling the document.
        """

        for parser in self.parsers:

            if parser.can_parse(text):
                return parser

        return None