import json
from abc import ABC, abstractmethod
from typing import List


class ParseResult:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_json(self):
        return json.dumps(self.__dict__)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, input_str: str) -> List[ParseResult]:
        """
        Abstract method that parses an input string and returns a dictionary.
        Must be implemented by subclasses.
        """
        pass

