from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from .w_types import *
from .tools import CustomToolTemplate
import json


# Workflow components
class Config(BaseModel):
    max_steps: int
    max_time: int
    tools: List[str] = Field(default_factory=list)
    custom_tools: Optional[List[Union[Dict, CustomToolTemplate]]] = None
    max_tokens: Optional[int] = None


class SearchQuery(BaseModel):
    value_type: InputValueType
    key: str


class InputValue(BaseModel):
    type: InputValueType
    index: Optional[int] = None
    search_query: Optional[SearchQuery] = None
    key: str


class Input(BaseModel):
    name: str
    value: InputValue
    required: bool


class Output(BaseModel):
    type: OutputType
    key: str
    value: str


class Task(BaseModel):
    id: str
    name: str
    description: str
    prompt: str
    inputs: List[Input] = Field(default_factory=list)
    operator: Operator
    outputs: List[Output] = Field(default_factory=list)


class TaskPostProcess(BaseModel):
    process_type: PostProcessType
    lhs: Optional[str] = None
    rhs: Optional[str] = None


class TaskOutput(BaseModel):
    input: InputValue
    to_json: Optional[bool] = None
    post_process: Optional[List[TaskPostProcess]] = None


class Condition(BaseModel):
    input: InputValue
    expected: str
    expression: Expression
    target_if_not: str


class Edge(BaseModel):
    source: str
    target: str
    condition: Optional[Condition] = None
    fallback: Optional[str] = None


class Entry(BaseModel):
    value: Union[str, dict]

    @classmethod
    def try_value_or_str(cls, s: str) -> "Entry":
        try:
            return cls(value=json.loads(s))
        except json.JSONDecodeError:
            return cls(value=s)

    def __str__(self):
        if isinstance(self.value, str):
            return self.value
        return json.dumps(self.value)


class StackPage(BaseModel):
    entries: List[Entry] = Field(default_factory=list)


class FilePage(BaseModel):
    name: str
    embeddings: List[float]
