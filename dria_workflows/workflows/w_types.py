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
    FUNCTION_CALLING_RAW = "function_calling_raw"
    SEARCH = "search"
    SAMPLE = "sample"
    END = "end"


class Expression(str, Enum):
    EQUAL = "Equal"
    NOT_EQUAL = "NotEqual"
    CONTAINS = "Contains"
    NOT_CONTAINS = "NotContains"
    GREATER_THAN = "GreaterThan"
    LESS_THAN = "LessThan"
    GREATER_THAN_OR_EQUAL = "GreaterThanOrEqual"
    LESS_THAN_OR_EQUAL = "LessThanOrEqual"
    HAVE_SIMILAR = "HaveSimilar"


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
    # Ollama models
    NOUS_THETA = "finalend/hermes-3-llama-3.1:8b-q8_0"
    PHI3_MEDIUM = "phi3:14b-medium-4k-instruct-q4_1"
    PHI3_MEDIUM_128K = "phi3:14b-medium-128k-instruct-q4_1"
    PHI3_5_MINI = "phi3.5:3.8b"
    PHI3_5_MINI_FP16 = "phi3.5:3.8b-mini-instruct-fp16"
    GEMMA2_9B = "gemma2:9b-instruct-q8_0"
    LLAMA3_1_8B = "llama3.1:latest"
    LLAMA3_1_8BQ8 = "llama3.1:8b-instruct-q8_0"

    # OpenAI models
    GPT3_5_TURBO = "gpt-3.5-turbo"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"


class ModelProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
