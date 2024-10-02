import json
import re
from typing import Dict, List
from .base import BaseParser, ParseResult


class NousParser(BaseParser):
    def parse(self, input_str: str) -> List[ParseResult]:
        """
        Parses a string containing a tool call in the format:
        <tool_call>
        {"arguments": <args-dict>, "name": <function-name>}
        </tool_call>

        Args:
            input_str (str): The string containing the tool call.

        Returns:
            Dict[str, Any]: A dictionary with 'name' and 'arguments' keys.

        Raises:
            ValueError: If the format is invalid or JSON parsing fails.
        """
        pattern = r"<tool_call>(.*?)</tool_call>"
        match = re.search(pattern, input_str, re.DOTALL)
        if not match:
            raise ValueError("Invalid format: <tool_call>...</tool_call> not found")

        json_str = match.group(1).strip()
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}")

        if not isinstance(data, dict):
            raise ValueError("Parsed content is not a JSON object")

        if 'name' not in data or 'arguments' not in data:
            raise ValueError("JSON object must contain 'name' and 'arguments' keys")
        return [ParseResult(**data)]


# Example usage:
if __name__ == "__main__":
    tool_call_response = """
    <tool_call>
    {
        "name": "Search Tool",
        "arguments": {
            "query": "example",
            "lang": "en",
            "n_results": 5
        }
    }
    </tool_call>
    """

    parser = NousParser()
    result = parser.parse(tool_call_response)
    print("Parsed Result:")
    print(result[0])