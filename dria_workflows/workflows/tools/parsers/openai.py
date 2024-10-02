import json
import re
from typing import Dict, List
from dria_workflows.workflows.tools.parsers.base import BaseParser, ParseResult


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
        pattern = r'\{[^{}]*\{[^{}]*\}[^{}]*\}'
        matches = re.findall(pattern, input_str, re.DOTALL)
        if not matches:
            raise ValueError("No function calls found in the input string.")

        result = []
        for tool_call_string in matches:
            tool_call_string = tool_call_string.strip().replace("```json", "").replace("```", "")
            try:
                tool_call = json.loads(tool_call_string)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON content': {e}")

            if not isinstance(tool_call['arguments'], dict):
                raise ValueError(f"Arguments for function '{tool_call['name']}' must be a JSON object.")

            result.append(ParseResult(name=tool_call['name'], arguments=tool_call['arguments']))

        return result


# Example usage:
if __name__ == "__main__":
    input_str = '''{\n "name": "calculator",\n "arguments": {\n  "lhs": 10932,\n  "rhs": 20934\n }\n}

{\n "name": "calculator",\n "arguments": {\n  "lhs": 10932,\n  "rhs": 20934\n }\n}'''

    parser = OpenAIParser()
    parsed_functions = parser.parse(input_str)
    print("Parsed Functions:")
    print(f"function lhs: {parsed_functions[0].arguments.lhs} rhs: lhs: {parsed_functions[0].arguments.rhs}")