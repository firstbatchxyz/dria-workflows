from typing import Dict, List, Optional, Union
from enum import Enum

class InputValueType(str, Enum):
    INPUT = "input"
    READ = "read"
    POP = "pop"
    PEEK = "peek"
    GET_ALL = "get_all"
    SIZE = "size"
    STRING = "string"

class OutputType(str, Enum):
    WRITE = "write"
    INSERT = "insert"
    PUSH = "push"

class Operator(str, Enum):
    GENERATION = "generation"
    FUNCTION_CALLING = "function_calling"
    SEARCH = "search"
    SAMPLE = "sample"
    END = "end"

class Expression(str, Enum):
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    HAVE_SIMILAR = "have_similar"

class PostProcessType(str, Enum):
    REPLACE = "replace"
    APPEND = "append"
    PREPEND = "prepend"
    TRIM = "trim"
    TRIM_START = "trim_start"
    TRIM_END = "trim_end"
    TO_LOWER = "to_lower"
    TO_UPPER = "to_upper"

class Model(str, Enum):
    NOUS_THETA = "adrienbrault/nous-hermes2theta-llama3-8b:q8_0"
    PHI3_MEDIUM = "phi3:14b-medium-4k-instruct-q4_1"
    PHI3_MEDIUM_128K = "phi3:14b-medium-128k-instruct-q4_1"
    PHI3_MINI = "phi3:3.8b"
    PHI3_5_MINI = "phi3.5:3.8b"
    PHI3_5_MINI_FP16 = "phi3.5:3.8b-mini-instruct-fp16"
    LLAMA3_1_8B = "llama3.1:latest"
    LLAMA3_1_8BQ8 = "llama3.1:8b-instruct-q8_0"
    GPT3_5_TURBO = "gpt-3.5-turbo"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"

class ModelProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"