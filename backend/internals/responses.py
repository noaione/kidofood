"""
MIT License

Copyright (c) 2022-present noaione

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

import orjson
from bson import ObjectId
from fastapi.responses import JSONResponse
from pendulum.datetime import DateTime
from pendulum.time import Time
from pydantic.generics import GenericModel

DataType = TypeVar("DataType")

__all__ = (
    "ORJSONXResponse",
    "ResponseType",
    "PaginationInfo",
    "PaginatedResponseType",
    "PaginatedMultiResponseType",
)


def ORJsonEncoder(obj: Any):  # noqa: N802
    if isinstance(obj, DateTime):
        return obj.for_json()
    if isinstance(obj, Time):
        return obj.for_json()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError


class ORJSONXResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return orjson.dumps(
            content,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
            default=ORJsonEncoder,
        )


class ResponseType(GenericModel, Generic[DataType]):
    error: str = "Success"
    code: int = 200
    data: Optional[DataType] = None

    def to_orjson(self, status: int = 200):
        return ORJSONXResponse(self.dict(), status_code=status)

    def to_string(self):
        data = self.dict()
        return orjson.dumps(data, default=ORJsonEncoder, option=orjson.OPT_INDENT_2 | orjson.OPT_SERIALIZE_UUID).decode(
            "utf-8"
        )

    class Config:
        schema_extra = {
            "example": {
                "data": None,
                "error": "Success",
                "code": 200,
            }
        }


@dataclass
class PaginationInfo:
    total: int
    """The total data count on all pages"""
    count: int
    """The current data count"""
    per_page: int
    """How much data exist per page"""
    next_cursor: Optional[str] = None
    """Next cursor for pagination"""


class PaginatedResponseType(GenericModel, Generic[DataType]):
    error: str = "Success"
    code: int = 200
    data: list[DataType] = []
    page_info: PaginationInfo

    def to_orjson(self, status: int = 200):
        return ORJSONXResponse(self.dict(), status_code=status)

    def to_string(self):
        data = self.dict()
        return orjson.dumps(data, default=ORJsonEncoder, option=orjson.OPT_INDENT_2 | orjson.OPT_SERIALIZE_UUID).decode(
            "utf-8"
        )

    class Config:
        schema_extra = {
            "example": {
                "data": [],
                "error": "Success",
                "code": 200,
                "page_info": {
                    "total": 0,
                    "count": 0,
                    "per_page": 0,
                    "next_cursor": None,
                },
            }
        }


class PaginatedMultiResponseType(GenericModel, Generic[DataType]):
    error: str = "Success"
    code: int = 200
    data: DataType = {}  # type: ignore
    page_info: dict[str, PaginationInfo] = {}

    def to_orjson(self, status: int = 200):
        return ORJSONXResponse(self.dict(), status_code=status)

    def to_string(self):
        data = self.dict()
        return orjson.dumps(data, default=ORJsonEncoder, option=orjson.OPT_INDENT_2 | orjson.OPT_SERIALIZE_UUID).decode(
            "utf-8"
        )

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "key1": [],
                },
                "error": "Success",
                "code": 200,
                "page_info": {
                    "key1": {
                        "total": 0,
                        "count": 0,
                        "per_page": 0,
                        "next_cursor": None,
                    },
                },
            }
        }
