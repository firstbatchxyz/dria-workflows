import json
from enum import Enum
from typing import (Any, Dict, List, Literal, Optional, Union, get_args,
                    get_origin)

from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class CustomToolMode(str, Enum):
    CUSTOM = "custom"
    HTTP_REQUEST = "http_request"


class ParameterProperty(BaseModel):
    type: str
    description: str


class CustomParameters(BaseModel):
    type: Literal["object"] = "object"
    properties: Dict[str, ParameterProperty]
    required: List[str]


class CustomToolModeTemplate(BaseModel):
    mode: CustomToolMode

    class Config:
        use_enum_values = True


class CustomToolCustom(CustomToolModeTemplate):
    mode: CustomToolMode = CustomToolMode.CUSTOM
    parameters: CustomParameters


class CustomToolHttpRequest(CustomToolModeTemplate):
    mode: CustomToolMode = CustomToolMode.HTTP_REQUEST
    url: str
    method: HttpMethod
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


class CustomToolTemplate(BaseModel):
    name: str
    description: str
    mode_template: Union[CustomToolCustom, CustomToolHttpRequest] = Field(..., alias="mode")

    class Config:
        populate_by_name = True

    def serialize_model(self):
        data = self.dict(by_alias=True, exclude_none=True)
        mode_template = data.pop('mode')
        data.update(mode_template)
        return data


class BaseTool(BaseModel):
    name: str
    description: str

    def get_parameters(self) -> Dict[str, Any]:
        properties = {}
        required = []
        for field_name, field_info in self.__fields__.items():
            if field_name in ['name', 'description']:
                continue
            json_type = self.python_type_to_json_type(field_info.annotation)
            properties[field_name] = {
                "type": json_type,
                "description": field_info.description or ""
            }
            if field_info.is_required():
                required.append(field_name)
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    @staticmethod
    def python_type_to_json_type(py_type):
        origin = get_origin(py_type)
        if origin is Union:
            args = get_args(py_type)
            non_none_types = [arg for arg in args if arg is not type(None)]
            if len(non_none_types) == 1:
                return BaseTool.python_type_to_json_type(non_none_types[0])
            else:
                return "object"
        elif py_type is str:
            return "string"
        elif py_type is int:
            return "integer"
        elif py_type is float:
            return "number"
        elif py_type is bool:
            return "boolean"
        elif py_type is dict:
            return "object"
        elif py_type is list:
            return "array"
        else:
            return "string"


class CustomTool(BaseTool, ABC):
    @abstractmethod
    def execute(self, **kwargs):
        pass


class HttpRequestTool(BaseTool):
    url: str
    method: HttpMethod
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


class ToolBuilder:
    @staticmethod
    def build_custom(tool_instance: CustomTool) -> CustomToolTemplate:
        parameters = tool_instance.get_parameters()
        custom_parameters = CustomParameters(**parameters)
        return CustomToolTemplate(
            name=tool_instance.name,
            description=tool_instance.description,
            mode=CustomToolCustom(parameters=custom_parameters)
        )

    @staticmethod
    def build_http_request(tool_instance: HttpRequestTool) -> CustomToolTemplate:
        return CustomToolTemplate(
            name=tool_instance.name,
            description=tool_instance.description,
            mode=CustomToolHttpRequest(
                url=tool_instance.url,
                method=tool_instance.method,
                headers=tool_instance.headers,
                body=tool_instance.body
            )
        )

    @staticmethod
    def build(tool_instance: BaseTool) -> CustomToolTemplate:
        if isinstance(tool_instance, CustomTool):
            return ToolBuilder.build_custom(tool_instance)
        elif isinstance(tool_instance, HttpRequestTool):
            return ToolBuilder.build_http_request(tool_instance)
        else:
            raise TypeError("Unsupported tool class type")


if __name__ == "__main__":
    class SearchTool(CustomTool):
        name: str = "Search Tool"
        description: str = "A tool that performs searches"
        query: str = Field(..., description="The search query")
        lang: Optional[str] = Field(None, description="The language for the search")
        n_results: Optional[int] = Field(None, description="The number of results to return")

    search_tool_instance = SearchTool(query="")
    search_tool = ToolBuilder.build(search_tool_instance)
    print("Search Tool:")
    print(json.dumps(search_tool.serialize_model(), indent=2))
    print()

    class MyHttpTool(HttpRequestTool):
        name: str = "HTTP Tool"
        description: str = "A tool that makes HTTP GET requests"
        url: str = "https://api.example.com/data"
        method: HttpMethod = HttpMethod.GET
        headers: Dict[str, str] = {"Authorization": "Bearer token123"}

    http_tool_instance = MyHttpTool()
    http_tool = ToolBuilder.build(http_tool_instance)
    print("HTTP Tool:")
    print(json.dumps(http_tool.serialize_model(), indent=2))
    print()