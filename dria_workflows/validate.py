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
                "description": "Analyze price feed",
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
    
    
    wf3 = {
  "config": {
    "max_steps": 50,
    "max_time": 200,
    "tools": [
      "ALL"
    ]
  },
  "external_memory": {
    "backstory": "Dr. Amelia Thornton, a brilliant 32-year-old physicist and engineer     living in London during the height of the Industrial Revolution in 1885.     She possesses an unparalleled understanding of mechanics, thermodynamics,     and material science, having studied under some of the era's greatest scientific minds.     Driven by an insatiable curiosity and a dream of human flight,     Amelia has dedicated her life to pushing the boundaries of what's possible.",
    "objective": "To design, construct, and successfully test the world's first powered, controlled, and sustained flying machine.      Conduct extensive research on aerodynamics and bird flight.      Develop and test various wing designs using scale models.      Acquire lightweight yet sturdy materials for construction.      Design and build a suitable engine for propulsion.      Construct a full-scale prototype.      Conduct rigorous safety tests and make necessary adjustments.     Attempt the first manned flight, documenting all results for scientific posterity",
    "behaviour": "Amelia approaches each day with meticulous planning and unwavering determination.     Her spending priorities are:     Essential materials and tools for experimentation and construction.     Scientific journals and books to stay abreast of the latest theories.     Networking with fellow inventors and potential investors.     Maintaining a modest lifestyle to maximize funds for her project.     She is cautious but not risk-averse, willing to make calculated gambles on promising innovations.     Amelia values precision, efficiency, and empirical evidence in all her decisions",
    "state": "",
    "inventory": [
      "Empty inventory"
    ]
  },
  "tasks": [
    {
      "id": "simulate",
      "name": "Task",
      "description": "Task Description",
      "prompt": "You are a sophisticated 317-dimensional alien world simulator capable of simulating any fictional or non-fictional world with excellent detail. Your task is to simulate one day in the life of a character based on the provided inputs, taking into account every given detail to accurately mimic the created world.\n\n---------------------\n\nYou just woke up to a new day. When you look at mirror as you wake up, you reflect on yourself and who you are. You are:\n<backstory>\n{{backstory}}\n</backstory>\n\nYou remember vividly what drove you in your life. You feel a strong urge to:\n<objective>\n{{objective}}\n</objective>\n\n\nTo be strong and coherent, you repeat out loud how you behave in front of the mirror.\n<behaviour>\n{{behaviour}}\n</behaviour>\n\nAs you recall who you are, what you do and your drive is, you write down to a notebook your current progress with your goal:\n<current_state>\n{{state}}\n</current_state>\n\nYou look through and see the items in your inventory.\n<inventory>\n{{inventory}}\n</inventory>\n\nFirst, an omnipotent being watches you through out the day outlining what you've been through today within your world in <observe> tags. This being is beyond time and space can understand slightest intentions also the complex infinite parameter world around you.\n\nYou live another day... It's been a long day and you write down your journal what you've achieved so far today, and what is left with your ambitions. It's only been a day, so you know that you can achieve as much that is possible within a day. \n\nWrite this is between <journal> tags.\nStart now:",
      "inputs": [
        {
          "name": "state",
          "value": {
            "type": "read",
            "key": "state"
          },
          "required": True
        },
        {
          "name": "backstory",
          "value": {
            "type": "read",
            "key": "backstory"
          },
          "required": True
        },
        {
          "name": "objective",
          "value": {
            "type": "read",
            "key": "objective"
          },
          "required": True
        },
        {
          "name": "behaviour",
          "value": {
            "type": "read",
            "key": "behaviour"
          },
          "required": True
        },
        {
          "name": "inventory",
          "value": {
            "type": "get_all",
            "key": "inventory"
          },
          "required": True
        }
      ],
      "operator": "generation",
      "outputs": [
        {
          "type": "write",
          "key": "new_state",
          "value": "__result"
        }
      ]
    },
    {
      "id": "_end",
      "name": "Task",
      "description": "Task Description",
      "prompt": "",
      "inputs": [],
      "operator": "end",
      "outputs": []
    }
  ],
  "steps": [
    {
      "source": "simulate",
      "target": "_end"
    }
  ],
  "return_value": {
    "input": {
      "type": "read",
      "key": "new_state"
    },
    "to_json": False
  }
}
    
    wf4 = {
  "config": {
    "max_steps": 50,
    "max_time": 200,
    "tools": [
      "ALL"
    ]
  },
  "external_memory": {
    "backstory": "Kyle Samani is the Co-Founder and Managing Partner of Multicoin Capital, a thesis-driven investment firm focused on cryptocurrencies, tokens, and blockchain companies13. Based in Austin, Texas, Samani is widely recognized as a thought leader on blockchain and cryptoeconomics. Samani and Multicoin Capital focus on three \"mega investment theses\" for crypto5:\nOpen Finance: Making units of value interoperable, programmable, and composable on open ledgers to create more accessible and efficient capital markets.\nWeb3: Reshaping the internet by creating new systems for storing and monetizing data, as well as new models for user acquisition and engagement.\nGlobal State-Free Money: The opportunity for a trust-minimized, natively digital bearer asset bound by physics, math, and free-market economics",
    "objective": "Kyle is highly optimistic about Solana's potential and skeptical of Ethereum's future. He believes Solana has a clear vision to become a \"global, real-time exchange,\" setting it apart from Ethereum, which he claims lacks a clear direction. Solana's faster transaction finality, just a few seconds compared to Ethereum's ~12 minutes, positions it well for capturing Maximal Extractable Value (MEV) and handling greater throughput. Innovations like token extensions, the Firedancer client, and hardware-based scaling show Solana’s ambition. Conversely, Kyle sees Ethereum as slow and directionless, with Layer 2s diverting value away from ETH. He aims to invest in Solana projects, envisioning a future where Solana dominates and Ethereum and Layer 2s are obsolete.\n\n\n\n\n\n\n",
    "behaviour": "Investing in top decentralized projects on the intersection of DePIN, DeFİ, decentralized AI and more.",
    "state": "",
    "inventory": [
      "Empty inventory"
    ]
  },
  "tasks": [
    {
      "id": "simulate",
      "name": "Task",
      "description": "Task Description",
      "prompt": "You are a sophisticated 317-dimensional alien world simulator capable of simulating any fictional or non-fictional world with excellent detail. Your task is to simulate one day in the life of a character based on the provided inputs, taking into account every given detail to accurately mimic the created world.\n\n---------------------\n\nYou just woke up to a new day. When you look at mirror as you wake up, you reflect on yourself and who you are. You are:\n<backstory>\n{{backstory}}\n</backstory>\n\nYou remember vividly what drove you in your life. You feel a strong urge to:\n<objective>\n{{objective}}\n</objective>\n\n\nTo be strong and coherent, you repeat out loud how you behave in front of the mirror.\n<behaviour>\n{{behaviour}}\n</behaviour>\n\nAs you recall who you are, what you do and your drive is, you write down to a notebook your current progress with your goal:\n<current_state>\n{{state}}\n</current_state>\n\nYou look through and see the items in your inventory.\n<inventory>\n{{inventory}}\n</inventory>\n\nFirst, an omnipotent being watches you through out the day outlining what you've been through today within your world in <observe> tags. This being is beyond time and space can understand slightest intentions also the complex infinite parameter world around you.\n\nYou live another day... It's been a long day and you write down your journal what you've achieved so far today, and what is left with your ambitions. It's only been a day, so you know that you can achieve as much that is possible within a day. \n\nWrite this is between <journal> tags.\nStart now:",
      "inputs": [
        {
          "name": "state",
          "value": {
            "type": "read",
            "key": "state"
          },
          "required": True
        },
        {
          "name": "backstory",
          "value": {
            "type": "read",
            "key": "backstory"
          },
          "required": True
        },
        {
          "name": "objective",
          "value": {
            "type": "read",
            "key": "objective"
          },
          "required": True
        },
        {
          "name": "behaviour",
          "value": {
            "type": "read",
            "key": "behaviour"
          },
          "required": True
        },
        {
          "name": "inventory",
          "value": {
            "type": "get_all",
            "key": "inventory"
          },
          "required": True
        }
      ],
      "operator": "generation",
      "outputs": [
        {
          "type": "write",
          "key": "new_state",
          "value": "__result"
        }
      ]
    },
    {
      "id": "_end",
      "name": "Task",
      "description": "Task Description",
      "prompt": "",
      "inputs": [],
      "operator": "end",
      "outputs": []
    }
  ],
  "steps": [
    {
      "source": "simulate",
      "target": "_end"
    }
  ],
  "return_value": {
    "input": {
      "type": "read",
      "key": "new_state"
    },
    "to_json": False
  }
}
    
    
    wf5 = {
  "config": {
    "max_steps": 50,
    "max_time": 200,
    "tools": [
      "ALL"
    ]
  },
  "external_memory": {
    "backstory": "Dr. Amelia Thornton, a brilliant 32-year-old physicist and engineer     living in London during the height of the Industrial Revolution in 1885.     She possesses an unparalleled understanding of mechanics, thermodynamics,     and material science, having studied under some of the era's greatest scientific minds.     Driven by an insatiable curiosity and a dream of human flight,     Amelia has dedicated her life to pushing the boundaries of what's possible.",
    "objective": "To design, construct, and successfully test the world's first powered, controlled, and sustained flying machine.      Conduct extensive research on aerodynamics and bird flight.      Develop and test various wing designs using scale models.      Acquire lightweight yet sturdy materials for construction.      Design and build a suitable engine for propulsion.      Construct a full-scale prototype.      Conduct rigorous safety tests and make necessary adjustments.     Attempt the first manned flight, documenting all results for scientific posterity",
    "behaviour": "Amelia approaches each day with meticulous planning and unwavering determination.     Her spending priorities are:     Essential materials and tools for experimentation and construction.     Scientific journals and books to stay abreast of the latest theories.     Networking with fellow inventors and potential investors.     Maintaining a modest lifestyle to maximize funds for her project.     She is cautious but not risk-averse, willing to make calculated gambles on promising innovations.     Amelia values precision, efficiency, and empirical evidence in all her decisions",
    "state": "",
    "inventory": [
      "Empty inventory"
    ]
  },
  "tasks": [
    {
      "id": "simulate",
      "name": "Task",
      "description": "Task Description",
      "prompt": "You are a sophisticated 317-dimensional alien world simulator capable of simulating any fictional or non-fictional world with excellent detail. Your task is to simulate one day in the life of a character based on the provided inputs, taking into account every given detail to accurately mimic the created world.\n\n---------------------\n\nYou just woke up to a new day. When you look at mirror as you wake up, you reflect on yourself and who you are. You are:\n<backstory>\n{{backstory}}\n</backstory>\n\nYou remember vividly what drove you in your life. You feel a strong urge to:\n<objective>\n{{objective}}\n</objective>\n\n\nTo be strong and coherent, you repeat out loud how you behave in front of the mirror.\n<behaviour>\n{{behaviour}}\n</behaviour>\n\nAs you recall who you are, what you do and your drive is, you write down to a notebook your current progress with your goal:\n<current_state>\n{{state}}\n</current_state>\n\nYou look through and see the items in your inventory.\n<inventory>\n{{inventory}}\n</inventory>\n\nFirst, an omnipotent being watches you through out the day outlining what you've been through today within your world in <observe> tags. This being is beyond time and space can understand slightest intentions also the complex infinite parameter world around you.\n\nYou live another day... It's been a long day and you write down your journal what you've achieved so far today, and what is left with your ambitions. It's only been a day, so you know that you can achieve as much that is possible within a day. \n\nWrite this is between <journal> tags.\nStart now:",
      "inputs": [
        {
          "name": "inventory",
          "value": {
            "type": "get_all",
            "key": "inventory"
          },
          "required": True
        },
        {
          "name": "objective",
          "value": {
            "type": "read",
            "key": "objective"
          },
          "required": True
        },
        {
          "name": "backstory",
          "value": {
            "type": "read",
            "key": "backstory"
          },
          "required": True
        },
        {
          "name": "behaviour",
          "value": {
            "type": "read",
            "key": "behaviour"
          },
          "required": True
        },
        {
          "name": "state",
          "value": {
            "type": "read",
            "key": "state"
          },
          "required": True
        }
      ],
      "operator": "generation",
      "outputs": [
        {
          "type": "write",
          "key": "new_state",
          "value": "__result"
        }
      ]
    },
    {
      "id": "_end",
      "name": "Task",
      "description": "Task Description",
      "prompt": "",
      "inputs": [],
      "operator": "end",
      "outputs": []
    }
  ],
  "steps": [
    {
      "source": "simulate",
      "target": "_end"
    }
  ],
  "return_value": {
    "input": {
      "type": "read",
      "key": "new_state"
    },
    "to_json": False
  }
}
    validate_workflow_json(json.dumps(wf5, indent=2))
