import json
from jsonschema import validate, ValidationError
import logging

# Define the JSON schema based on the Rust struct
schema = {
    "type": "object",
    "properties": {
        "config": {
            "type": "object",
            "properties": {
                "max_steps": {"type": "integer", "minimum": 0},
                "max_time": {"type": "integer", "minimum": 0},
                "tools": {"type": "array", "items": {"type": "string"}},
                "custom_tools": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "mode": {"type": "string"},
                            "url": {"type": "string"},
                            "method": {"type": "string"},
                            "headers": {"type": "object"},
                            "body": {"type": "object"},
                        },
                        "required": ["name", "description", "mode"],
                    },
                },
                "max_tokens": {"type": ["integer", "null"], "minimum": 0},
            },
            "required": ["max_steps", "max_time"],
        },
        "external_memory": {
            "type": "object",
            "additionalProperties": {
                "oneOf": [
                    {
                        "type": "array",
                        "items": {"oneOf": [{"type": "string"}, {"type": "object"}]},
                    },
                    {"type": "string"},
                ]
            },
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "prompt": {"type": "string"},
                    "inputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "input",
                                                "read",
                                                "pop",
                                                "peek",
                                                "get_all",
                                                "size",
                                                "string",
                                            ],
                                        },
                                        "index": {"type": ["integer", "null"]},
                                        "search_query": {
                                            "type": "object",
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "enum": [
                                                        "input",
                                                        "read",
                                                        "pop",
                                                        "peek",
                                                        "get_all",
                                                        "size",
                                                        "string",
                                                    ],
                                                },
                                                "key": {"type": "string"},
                                            },
                                            "required": ["type", "key"],
                                        },
                                        "key": {"type": "string"},
                                    },
                                    "required": ["type", "key"],
                                },
                                "required": {"type": "boolean"},
                            },
                            "required": ["name", "value", "required"],
                        },
                    },
                    "operator": {
                        "type": "string",
                        "enum": [
                            "generation",
                            "function_calling",
                            "function_calling_raw",
                            "check",
                            "search",
                            "sample",
                            "end",
                        ],
                    },
                    "outputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["write", "insert", "push"],
                                },
                                "key": {"type": "string"},
                                "value": {"type": "string"},
                            },
                            "required": ["type", "key", "value"],
                        },
                    },
                },
                "required": ["id", "name", "description", "prompt", "operator"],
            },
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "condition": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": [
                                            "input",
                                            "read",
                                            "pop",
                                            "peek",
                                            "get_all",
                                            "size",
                                            "string",
                                        ],
                                    },
                                    "key": {"type": "string"},
                                },
                                "required": ["type", "key"],
                            },
                            "expected": {"type": "string"},
                            "expression": {
                                "type": "string",
                                "enum": [
                                    "Equal",
                                    "NotEqual",
                                    "Contains",
                                    "NotContains",
                                    "GreaterThan",
                                    "LessThan",
                                    "GreaterThanOrEqual",
                                    "LessThanOrEqual",
                                    "HaveSimilar",
                                ],
                            },
                            "target_if_not": {"type": "string"},
                        },
                        "required": [
                            "input",
                            "expected",
                            "expression",
                            "target_if_not",
                        ],
                    },
                    "fallback": {"type": "string"},
                },
                "required": ["source", "target"],
            },
        },
        "return_value": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "input",
                                "read",
                                "pop",
                                "peek",
                                "get_all",
                                "size",
                                "string",
                            ],
                        },
                        "key": {"type": "string"},
                    },
                    "required": ["type", "key"],
                },
                "to_json": {"type": "boolean"},
                "post_process": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "process_type": {
                                "type": "string",
                                "enum": [
                                    "replace",
                                    "append",
                                    "prepend",
                                    "trim",
                                    "trim_start",
                                    "trim_end",
                                    "to_lower",
                                    "to_upper",
                                ],
                            },
                            "lhs": {"type": "string"},
                            "rhs": {"type": "string"},
                        },
                        "required": ["process_type"],
                    },
                },
            },
            "required": ["input"],
        },
    },
    "required": ["config", "tasks", "steps", "return_value"],
}


def validate_workflow_json(json_data):
    try:
        # Parse the JSON data
        workflow = json.loads(json_data)

        # Validate the JSON against the schema
        validate(instance=workflow, schema=schema)

        logging.info("The JSON is valid and serializable to the Workflow struct.")
        return True
    except json.JSONDecodeError as e:
        logging.info(f"Invalid JSON: {e}")
        return False
    except ValidationError as e:
        logging.info(f"JSON does not match the Workflow struct: {e}")
        return False


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    wf = {
        "name": "Custom Tool",
        "description": "This is a simple workflow for custom tools",
        "config":{
            "max_steps": 5,
            "max_time": 100,
            "max_tokens": 1024,
            "tools": [],
            "custom_tools":[{
                "name": "PriceFeedRequest",
                "description": "Fetches price feed from Gemini API",
                "mode":"http_request",
                "url": "https://api.gemini.com/v1/pricefeed",
                "method": "GET"
              }]
        },
        "tasks":[
            {
                "id": "A",
                "name": "Get prices",
                "description": "Get price feed",
                "prompt": "What are the current prices?",
                "inputs":[],
                "operator": "function_calling",
                "outputs":[
                    {
                        "type": "write",
                        "key": "prices",
                        "value": "__result"
                    }
                ]
            },
            {
                "id": "B",
                "name": "Analyze prices",
                "description": "Anzlye price feed",
                "prompt": "Context: <prices>{prices}</prices> \n\n Use the context to find which ticker pair had the highest price change in 24 and has a price above $300?",
                "inputs":[
                    {
                        "name": "prices",
                        "value": {
                            "type": "read",
                            "key": "prices"
                        },
                        "required": True
                    }
                ],
                "operator": "generation",
                "outputs":[
                    {
                        "type": "write",
                        "key": "result",
                        "value": "__result"
                    }
                ]
            },
            {
                "id": "__end",
                "name": "end",
                "description": "End of the task",
                "prompt": "End of the task",
                "inputs": [],
                "operator": "end",
                "outputs": []
            }
        ],
        "steps":[
            {
                "source":"A",
                "target":"B"
            },
            {
                "source":"B",
                "target":"end"
            }
        ],
        "return_value":{
            "input":{
                "type": "read",
                "key": "result"
            }
        }
    }

    wf2 = {'config': {'max_steps': 50, 'max_time': 200, 'tools': ['ALL'], 'custom_tools': [{'name': 'calculator', 'description': 'A tool sums integers', 'mode': 'custom', 'parameters': {'type': 'object', 'properties': {'lfs': {'type': 'integer', 'description': 'Left hand side of sum'}, 'rhs': {'type': 'integer', 'description': 'Right hand side of sum'}}, 'required': []}}]}, 'external_memory': {}, 'tasks': [{'id': 'sum', 'name': 'Task', 'description': 'Task Description', 'prompt': 'What is 10932 + 20934?', 'inputs': [], 'operator': 'function_calling_raw', 'outputs': [{'type': 'write', 'key': 'call', 'value': '__result'}]}, {'id': '_end', 'name': 'Task', 'description': 'Task Description', 'prompt': '', 'inputs': [], 'operator': 'end', 'outputs': []}], 'steps': [{'source': 'sum', 'target': '_end'}], 'return_value': {'input': {'type': 'read', 'key': 'call'}, 'to_json': False}}

    validate_workflow_json(json.dumps(wf2, indent=2))
