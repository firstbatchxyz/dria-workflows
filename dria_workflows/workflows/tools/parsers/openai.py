import json
import re
from typing import Dict, List
from .base import BaseParser, ParseResult


class OpenAIParser(BaseParser):
    def parse(self, input_str: str) -> List[ParseResult]:
        """
        Parses a string containing function calls in the format:
        Function: function_name
        Arguments: JSON_arguments

        Args:
            input_str (str): The string containing the function calls.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with 'name' and 'arguments' keys.

        Raises:
            ValueError: If the format is invalid or JSON parsing fails.
        """
        pattern = r"Function:\s*(.+?)\nArguments:\s*(\{.*?\})(?:\n|$)"
        matches = re.findall(pattern, input_str, re.DOTALL)
        if not matches:
            raise ValueError("No function calls found in the input string.")

        result = []
        for func_name, json_str in matches:
            func_name = func_name.strip()
            json_str = json_str.strip()
            try:
                arguments = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON content in function '{func_name}': {e}")

            if not isinstance(arguments, dict):
                raise ValueError(f"Arguments for function '{func_name}' must be a JSON object.")

            result.append(ParseResult(name=func_name.strip(), arguments=arguments))

        return result


# Example usage:
if __name__ == "__main__":
    input_str = '''Function: google_search_tool
Arguments: {"query": "most famous street in Istanbul"}

Function: google_search_tool
Arguments: {"query": "longest river in the world"}'''

    parser = OpenAIParser()
    parsed_functions = parser.parse(input_str)
    print("Parsed Functions:")
    print(json.dumps(parsed_functions, indent=2))