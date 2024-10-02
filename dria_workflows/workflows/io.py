from pydantic import BaseModel, Field
from typing import Optional, List, Union
from .interface import (
    Input,
    Output,
    InputValueType,
    InputValue,
    Task,
    TaskOutput,
    Condition,
    Config,
    OutputType,
)


class Read:
    """
    A utility class for creating Input objects with READ value type.

    This class provides a static method to create Input objects specifically
    for reading values from the workflow's memory.
    """
    @staticmethod
    def new(key: str, required: bool) -> Input:
        return Input(
            name=key,
            value=InputValue(type=InputValueType.READ, key=key),
            required=required,
        )


class Pop:
    """
    A utility class for creating Input objects with POP value type.

    This class provides a static method to create Input objects specifically
    for popping values from the workflow's memory.
    """

    @staticmethod
    def new(key: str, required: bool) -> Input:
        return Input(
            name=key,
            value=InputValue(type=InputValueType.POP, key=key),
            required=required,
        )


class Peek:
    """
    A utility class for creating Input objects with PEEK value type.

    This class provides a static method to create Input objects specifically
    for peeking at values in the workflow's memory without removing them.
    """

    @staticmethod
    def new(key: str, index: int, required: bool) -> Input:
        return Input(
            name=key,
            value=InputValue(type=InputValueType.PEEK, key=key, index=index),
            required=required,
        )


class GetAll:
    """
    A utility class for creating Input objects with GET_ALL value type.

    This class provides a static method to create Input objects specifically
    for retrieving all values associated with a key from the workflow's memory.
    """

    @staticmethod
    def new(key: str, required: bool) -> Input:
        return Input(
            name=key,
            value=InputValue(type=InputValueType.GET_ALL, key=key),
            required=required,
        )


class Size:
    """
    A utility class for creating Input objects with SIZE value type.

    This class provides a static method to create Input objects specifically
    for getting the size of a collection in the workflow's memory.
    """

    @staticmethod
    def new(key: str, required: bool) -> Input:
        return Input(
            name=key,
            value=InputValue(type=InputValueType.SIZE, key=key),
            required=required,
        )


class String:
    """
    A utility class for creating Input objects with STRING value type.

    This class provides a static method to create Input objects specifically
    for string literals in the workflow.
    """

    @staticmethod
    def new(key: str, value: str, required: bool) -> Input:
        return Input(
            name=key,
            value=InputValue(type=InputValueType.STRING, key=value),
            required=required,
        )


class Write:
    """
    A utility class for creating Output objects with WRITE value type.

    This class provides a static method to create Output objects specifically
    for writing values to the workflow's memory.
    """

    @staticmethod
    def new(key: str) -> Output:
        return Output(type=OutputType.WRITE, key=key, value="__result")


class Insert:
    """
    A utility class for creating Output objects with INSERT value type.

    This class provides a static method to create Output objects specifically
    for inserting values into a list in the workflow's memory.
    """

    @staticmethod
    def new(key: str) -> Output:
        return Output(type=OutputType.INSERT, key=key, value="__result")


class Push:
    """
    A utility class for creating Output objects with PUSH value type.

    This class provides a static method to create Output objects specifically
    for pushing values onto a list in the workflow's memory.
    """

    @staticmethod
    def new(key: str) -> Output:
        return Output(type=OutputType.PUSH, key=key, value="__result")


INPUTS = Union[Read, GetAll, Size, Peek, Pop]
OUTPUTS = Union[Write, Insert, Push]
