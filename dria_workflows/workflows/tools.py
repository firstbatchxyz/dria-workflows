from pydantic import BaseModel
from typing import Optional, List, Union, Dict
from enum import Enum


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class CustomToolTemplate(BaseModel):
    name: str
    description: str
    url: str
    method: HttpMethod
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, str]] = None


class CustomToolBuilder:
    @staticmethod
    def build(
        name: str,
        description: str,
        url: str,
        method: HttpMethod,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, str]] = None,
    ) -> CustomToolTemplate:
        # Validate URL
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with 'http://' or 'https://'")

        # Validate headers
        if headers:
            if not all(
                isinstance(k, str) and isinstance(v, str) for k, v in headers.items()
            ):
                raise ValueError("All header keys and values must be strings")

        # Validate body for methods that typically have a body
        if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            if body is None:
                raise ValueError(f"{method.value} requests typically require a body")
        elif body is not None:
            raise ValueError(f"{method.value} requests typically do not have a body")

        return CustomToolTemplate(
            name=name,
            description=description,
            url=url,
            method=method,
            headers=headers,
            body=body,
        )
