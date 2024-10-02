import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from types import SimpleNamespace


class ParseResult:
    name: str
    arguments: Any

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        arguments_dict = kwargs.get("arguments")
        if not self.name or not arguments_dict:
            raise ValueError("Both 'name' and 'arguments' are required.")
        self.arguments = SimpleNamespace(**arguments_dict)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, input_str: str) -> List[ParseResult]:
        """
        Abstract method that parses an input string and returns a dictionary.
        Must be implemented by subclasses.
        """
        pass

