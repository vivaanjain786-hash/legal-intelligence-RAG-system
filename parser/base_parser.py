from abc import ABC, abstractmethod


class BaseParser(ABC):

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """
        Determine whether this parser can handle the document.
        """
        pass

    @abstractmethod
    def parse(self, text: str) -> dict:
        """
        Extract structured metadata from the document.
        """
        pass