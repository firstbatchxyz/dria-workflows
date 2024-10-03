import json
from abc import ABC, abstractmethod
from typing import List, Type, Any
from types import SimpleNamespace
from dria_workflows.workflows.tools import CustomTool

class ParseResult:
    name: str
    arguments: Any

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        arguments_dict = kwargs.get("arguments")
        if not self.name or not arguments_dict:
            raise ValueError("Both 'name' and 'arguments' are required.")
        self.arguments = SimpleNamespace(**arguments_dict)

    def execute(self, tools: List[Type[CustomTool]], **kwargs):

        if any(not issubclass(tool_class, CustomTool) for tool_class in tools):
            invalid_classes = [tool_class.__name__ for tool_class in tools if not issubclass(tool_class, CustomTool)]
            raise ValueError(f"Classes {invalid_classes} are not subclasses of 'CustomTool'. "
                             f"Method 'execute' can only be called with subclasses of 'CustomTool'.")

        for tool_class in tools:
            try:
                tool = tool_class(**self.arguments.__dict__)
                if tool.name == self.name:
                    return tool.execute(**kwargs)
            except TypeError:
                continue

        # If no matching tool is found after iterating through all tools
        raise ValueError(f"Tool '{self.name}' not found in the provided list.")


class BaseParser(ABC):
    @abstractmethod
    def parse(self, input_str: str) -> List[ParseResult]:
        """
        Abstract method that parses an input string and returns a dictionary.
        Must be implemented by subclasses.
        """
        pass

