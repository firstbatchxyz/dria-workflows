import json
import re
from typing import Dict, List
from .base import BaseParser, ParseResult


class LlamaParser(BaseParser):
    def parse(self, input_str: str) -> List[ParseResult]:
        """
        Parses a string containing function calls in the format:
        <function=function_name>{{JSON_arguments}}</function>

        Args:
            input_str (str): The string containing the function calls.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with 'name' and 'arguments' keys.

        Raises:
            ValueError: If the format is invalid or JSON parsing fails.
        """
        pattern = r"<function=(\w+)>(.*?)</function>"
        matches = re.findall(pattern, input_str, re.DOTALL)
        if not matches:
            raise ValueError("No function calls found in the input string.")

        result = []
        for func_name, json_str in matches:
            json_str = json_str.strip()
            try:
                arguments = json.loads(json_str.replace("{{", "{").replace("}}", "}"))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON content in function '{func_name}': {e}")

            if not isinstance(arguments, dict):
                raise ValueError(f"Arguments for function '{func_name}' must be a JSON object.")

            result.append(ParseResult(name=func_name.strip(), arguments=arguments))

        return result


# Example usage:
if __name__ == "__main__":
    input_str = '''
    <function=google_search_tool>{{"query": "most famous street in Istanbul", "lang": "en", "n_results": 1}}</function>
    <function=google_search_tool>{{"query": "longest river in the world", "lang": "en", "n_results": 1}}</function>
    '''

    parser = LlamaParser()
    parsed_functions = parser.parse(input_str)
    print("Parsed Functions:")
    print(parsed_functions[0].__dict__)